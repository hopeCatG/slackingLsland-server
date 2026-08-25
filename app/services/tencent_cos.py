from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from qcloud_cos import CosConfig, CosS3Client
from sqlalchemy.orm import Session

from app.services.system_config import ConfigNotFoundError, get_required_config_value

_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_MAX_AVATAR_BYTES = 5 * 1024 * 1024


def _get_client(db: Session) -> tuple[CosS3Client, str, str]:
    """从 system_config 构建腾讯云 COS 客户端。"""
    try:
        bucket = get_required_config_value(db, "TENCENT_COS_BUCKET")
        secret_id = get_required_config_value(db, "TENCENT_COS_SECRET_ID")
        secret_key = get_required_config_value(db, "TENCENT_COS_SECRET_KEY")
        region = get_required_config_value(db, "TENCENT_COS_REGION")
        domain = get_required_config_value(db, "TENCENT_COS_DOMAIN")
    except ConfigNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Scheme="https")
    return CosS3Client(config), bucket, domain.rstrip("/")


async def upload_static_image(db: Session, file: UploadFile, directory: str = "uploads") -> str:
    """上传静态图片，返回腾讯云 COS 的可访问地址。"""
    suffix = Path(file.filename or "").suffix.lower()
    if file.content_type not in _IMAGE_CONTENT_TYPES or suffix not in _IMAGE_SUFFIXES:
        raise HTTPException(status_code=400, detail="仅支持 JPG、PNG、WEBP、GIF 格式的图片")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传文件不能为空")
    if len(content) > _MAX_AVATAR_BYTES:
        raise HTTPException(status_code=400, detail="头像图片不能超过 5MB")

    client, bucket, domain = _get_client(db)
    date_path = datetime.now(UTC).strftime("%Y/%m/%d")
    object_key = f"{directory}/{date_path}/{uuid4().hex}{suffix}"
    try:
        client.put_object(Bucket=bucket, Key=object_key, Body=content, ContentType=file.content_type)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="头像上传失败，请稍后重试") from exc

    return f"{domain if domain.startswith(('http://', 'https://')) else f'https://{domain}'}/{object_key}"


async def upload_avatar(db: Session, file: UploadFile) -> str:
    """上传用户头像到固定的 avatars 目录。"""
    return await upload_static_image(db, file, directory="avatars")
