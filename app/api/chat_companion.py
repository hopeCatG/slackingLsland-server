from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.users import get_current_user
from app.core.response import success_response
from app.database import get_db
from app.models.chat_companion import ChatCompanionMessage, ChatCompanionSession
from app.models.mini_user import WxMiniUser
from app.schemas.chat_companion import CreateChatSessionRequest, SendChatMessageRequest
from app.services.dify_chat import stream_dify_reply
from app.services.system_config import ConfigNotFoundError, get_config_value, get_required_config_value

router = APIRouter(prefix="/chat-companion", tags=["聊天搭子"])


def _session_data(item: ChatCompanionSession) -> dict:
    return {
        "sessionId": item.session_no,
        "topic": item.topic,
        "mood": item.mood,
        "eventDetail": item.event_detail,
        "title": item.title,
        "lastMessageAt": item.last_message_at.isoformat() if item.last_message_at else None,
        "createdAt": item.created_at.isoformat(),
    }


def _owned_session(db: Session, session_no: str, user_id: int) -> ChatCompanionSession:
    item = db.scalar(
        select(ChatCompanionSession).where(
            ChatCompanionSession.session_no == session_no,
            ChatCompanionSession.user_id == user_id,
            ChatCompanionSession.status == 1,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="聊天会话不存在")
    return item


@router.post("/sessions", summary="创建聊天搭子会话")
async def create_session(
    payload: CreateChatSessionRequest,
    db: Session = Depends(get_db),
    user: WxMiniUser = Depends(get_current_user),
) -> dict:
    topic = payload.topic.strip()
    mood = payload.mood.strip()
    event_detail = payload.eventDetail.strip()
    if not topic or not mood or len(event_detail) < 2:
        raise HTTPException(status_code=422, detail="请把想吐槽的事再说具体一点")
    item = ChatCompanionSession(
        session_no=uuid4().hex,
        user_id=user.id,
        topic=topic,
        mood=mood,
        event_detail=event_detail,
        title=f"{topic} · {mood}",
        last_message_at=datetime.now(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return success_response(_session_data(item))


@router.get("/sessions", summary="获取我的聊天历史")
async def list_sessions(
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    user: WxMiniUser = Depends(get_current_user),
) -> dict:
    items = db.scalars(
        select(ChatCompanionSession)
        .where(ChatCompanionSession.user_id == user.id, ChatCompanionSession.status == 1)
        .order_by(desc(ChatCompanionSession.last_message_at), desc(ChatCompanionSession.id))
        .limit(limit)
    ).all()
    return success_response([_session_data(item) for item in items])


@router.get("/sessions/{session_no}", summary="获取会话和消息")
async def get_session(
    session_no: str,
    db: Session = Depends(get_db),
    user: WxMiniUser = Depends(get_current_user),
) -> dict:
    item = _owned_session(db, session_no, user.id)
    messages = db.scalars(
        select(ChatCompanionMessage)
        .where(ChatCompanionMessage.session_id == item.id, ChatCompanionMessage.status == 1)
        .order_by(ChatCompanionMessage.id)
    ).all()
    data = _session_data(item)
    data["messages"] = [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "createdAt": message.created_at.isoformat(),
        }
        for message in messages
    ]
    return success_response(data)


@router.post("/sessions/{session_no}/messages/stream", summary="发送消息并流式获取回复")
async def send_message(
    session_no: str,
    payload: SendChatMessageRequest,
    db: Session = Depends(get_db),
    user: WxMiniUser = Depends(get_current_user),
) -> StreamingResponse:
    item = _owned_session(db, session_no, user.id)
    try:
        api_key = get_required_config_value(db, "DIFY_CHAT_API_KEY")
    except ConfigNotFoundError as exc:
        raise HTTPException(status_code=503, detail="聊天搭子尚未配置，请联系管理员") from exc
    if api_key == "YOUR_DIFY_APP_API_KEY":
        raise HTTPException(status_code=503, detail="请先在 system_config 中填写 Dify App API Key")
    api_base_url = get_config_value(db, "DIFY_CHAT_BASE_URL", "http://word.skyblue.chat/v1")
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="消息不能为空")
    return StreamingResponse(
        stream_dify_reply(
            session_id=item.id,
            user_id=user.id,
            content=content,
            api_base_url=api_base_url or "http://word.skyblue.chat/v1",
            api_key=api_key,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
