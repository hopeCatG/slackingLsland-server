import json
from collections.abc import AsyncGenerator
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.chat_companion import ChatCompanionMessage, ChatCompanionSession


def _sse(event: str, data: dict) -> str:
    # ensure_ascii 让微信小程序按字节拆包时也能安全拼接 JSON，JSON.parse 会还原中文。
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=True, separators=(',', ':'))}\n\n"


def _save_user_message(session_id: int, content: str) -> None:
    with SessionLocal() as db:
        chat_session = db.get(ChatCompanionSession, session_id)
        if chat_session is None:
            return
        now = datetime.now()
        db.add(ChatCompanionMessage(session_id=session_id, role="user", content=content))
        chat_session.last_message_at = now
        db.commit()


def _finish_assistant_message(
    session_id: int,
    content: str,
    dify_message_id: str | None,
    conversation_id: str | None,
) -> None:
    with SessionLocal() as db:
        chat_session = db.get(ChatCompanionSession, session_id)
        if chat_session is None:
            return
        if content:
            db.add(
                ChatCompanionMessage(
                    session_id=session_id,
                    role="assistant",
                    content=content,
                    dify_message_id=dify_message_id,
                )
            )
        if conversation_id:
            chat_session.dify_conversation_id = conversation_id
        chat_session.last_message_at = datetime.now()
        db.commit()


async def stream_dify_reply(
    *,
    session_id: int,
    user_id: int,
    content: str,
    api_base_url: str,
    api_key: str,
) -> AsyncGenerator[str, None]:
    _save_user_message(session_id, content)

    with SessionLocal() as db:
        chat_session = db.get(ChatCompanionSession, session_id)
        if chat_session is None:
            yield _sse("error", {"message": "会话不存在"})
            return
        payload = {
            "inputs": {
                "吐槽主题": chat_session.topic,
                "当前情绪": chat_session.mood,
                "具体事件": chat_session.event_detail,
            },
            "query": content,
            "response_mode": "streaming",
            "conversation_id": chat_session.dify_conversation_id or "",
            "user": f"wx-mini-{user_id}",
        }

    answer = ""
    conversation_id: str | None = None
    message_id: str | None = None
    completed = False
    try:
        timeout = httpx.Timeout(connect=15.0, read=180.0, write=30.0, pool=15.0)
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST", f"{api_base_url.rstrip('/')}/chat-messages", headers=headers, json=payload
            ) as response:
                if response.status_code >= 400:
                    raw = (await response.aread()).decode("utf-8", errors="replace")
                    try:
                        detail = json.loads(raw).get("message") or "Dify 服务请求失败"
                    except json.JSONDecodeError:
                        detail = "Dify 服务请求失败"
                    yield _sse("error", {"message": detail, "statusCode": response.status_code})
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw_data = line[5:].strip()
                    if not raw_data:
                        continue
                    try:
                        data = json.loads(raw_data)
                    except json.JSONDecodeError:
                        continue
                    event = data.get("event")
                    conversation_id = data.get("conversation_id") or conversation_id
                    message_id = data.get("message_id") or message_id
                    if event in {"agent_message", "message"}:
                        chunk = data.get("answer") or ""
                        if chunk:
                            answer += chunk
                            yield _sse("message", {"answer": chunk})
                    elif event == "message_replace":
                        answer = data.get("answer") or ""
                        yield _sse("replace", {"answer": answer})
                    elif event == "message_end":
                        completed = True
                        break
                    elif event == "error":
                        yield _sse("error", {"message": data.get("message") or "聊天服务暂时开小差了"})
                        return
        completed = True
    except httpx.TimeoutException:
        yield _sse("error", {"message": "搭子想得有点久，请稍后重试"})
    except httpx.HTTPError:
        yield _sse("error", {"message": "暂时连接不上聊天搭子，请稍后重试"})
    finally:
        if answer:
            _finish_assistant_message(session_id, answer, message_id, conversation_id)
        if completed:
            yield _sse(
                "done",
                {"conversationId": conversation_id or "", "messageId": message_id or ""},
            )
