from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.response import success_response
from app.database import get_db
from app.services.tencent_cos import upload_avatar, upload_static_image

router = APIRouter(prefix="/storage", tags=["文件存储"])


@router.post("/upload", summary="上传静态图片到腾讯云 COS")
async def upload_static_file(
    file: UploadFile = File(...),
    directory: str = Query(default="uploads", pattern="^(uploads|images|avatars)$"),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(data={"url": await upload_static_image(db, file, directory)})


@router.post("/avatar", summary="上传小程序用户头像")
async def upload_user_avatar(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    return success_response(data={"url": await upload_avatar(db, file)})
