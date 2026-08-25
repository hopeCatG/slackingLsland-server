from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import success_response
from app.database import get_db
from app.models.mini_user import WxMiniUser
from app.schemas.auth import WechatLoginRequest
from app.services.wechat_auth import create_access_token, exchange_code

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/wechat/login", summary="微信小程序登录")
async def wechat_login(payload: WechatLoginRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    openid, unionid = await exchange_code(db, payload.code)
    client_ip = request.client.host if request.client else None
    user = db.scalar(select(WxMiniUser).where(WxMiniUser.openid == openid))

    nickname = payload.nickname.strip() if payload.nickname else None
    avatar_url = payload.avatar_url.strip() if payload.avatar_url else None
    if bool(nickname) != bool(avatar_url):
        raise HTTPException(status_code=422, detail="昵称和头像需要同时提交")

    # 第一次仅通过 code 查询账号：已有完整资料的用户无需再次授权头像和昵称。
    if user is None and not nickname:
        return success_response(data={"needProfile": True}, message="请完善头像和昵称")

    if user is None:
        user = WxMiniUser(openid=openid, unionid=unionid, nickname=nickname, avatar_url=avatar_url, last_login_at=datetime.now(), last_login_ip=client_ip, login_count=1)
        db.add(user)
    else:
        if user.status != 1:
            raise HTTPException(status_code=403, detail="该账号不可用")
        if (not user.nickname or not user.avatar_url) and not nickname:
            return success_response(data={"needProfile": True}, message="请完善头像和昵称")
        user.unionid = unionid or user.unionid
        if nickname:
            user.nickname = nickname
            user.avatar_url = avatar_url
        user.last_login_at = datetime.now()
        user.last_login_ip = client_ip
        user.login_count += 1
    db.commit()
    db.refresh(user)
    return success_response(data={
        "needProfile": False,
        "accessToken": create_access_token(user.id),
        "user": {"id": user.id, "nickname": user.nickname, "avatarUrl": user.avatar_url, "isNew": user.login_count == 1},
    })
