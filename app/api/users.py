from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.response import success_response
from app.database import get_db
from app.models.mini_user import WxMiniUser
from app.schemas.auth import UpdateUserProfileRequest
from app.services.wechat_auth import get_token_user_id

router = APIRouter(prefix="/users", tags=["用户"])


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> WxMiniUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    user = db.get(WxMiniUser, get_token_user_id(authorization[7:].strip()))
    if user is None or user.status != 1:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return user


@router.put("/me", summary="修改当前用户资料")
async def update_my_profile(
    payload: UpdateUserProfileRequest,
    db: Session = Depends(get_db),
    user: WxMiniUser = Depends(get_current_user),
) -> dict:
    user.nickname = payload.nickname.strip()
    user.avatar_url = payload.avatar_url.strip()
    db.commit()
    db.refresh(user)
    return success_response(data={"id": user.id, "nickname": user.nickname, "avatarUrl": user.avatar_url})
