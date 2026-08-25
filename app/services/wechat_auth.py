import base64
import hashlib
import hmac
import json
import time

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.system_config import ConfigNotFoundError, get_required_config_value


async def exchange_code(db: Session, code: str) -> tuple[str, str | None]:
    """使用小程序 code 换取微信真实 openid。"""
    try:
        app_id = get_required_config_value(db, "WECHAT_APP_ID")
        app_secret = get_required_config_value(db, "WECHAT_APP_SECRET")
    except ConfigNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    params = {
        "appid": app_id,
        "secret": app_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get("https://api.weixin.qq.com/sns/jscode2session", params=params)
    payload = response.json()
    if payload.get("errcode") or not payload.get("openid"):
        raise HTTPException(status_code=401, detail=payload.get("errmsg", "微信登录凭证无效"))
    return payload["openid"], payload.get("unionid")


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    payload = {"sub": user_id, "exp": int(time.time()) + 7 * 24 * 3600}
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(settings.token_secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def get_token_user_id(token: str) -> int:
    """验证本服务签发的访问令牌并返回用户 ID。"""
    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(get_settings().token_secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        padded = encoded + "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if int(payload["exp"]) <= int(time.time()):
            raise ValueError("expired")
        return int(payload["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录") from exc
