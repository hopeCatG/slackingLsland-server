from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig


class ConfigNotFoundError(LookupError):
    """请求的配置不存在、未启用或值为空。"""


def get_config_value(db: Session, config_key: str, default: str | None = None) -> str | None:
    """获取一个已启用的系统配置值；不存在时返回 default。"""
    value = db.scalar(
        select(SystemConfig.config_value).where(
            SystemConfig.config_key == config_key,
            SystemConfig.is_enabled == 1,
        )
    )
    return value if value not in (None, "") else default


def get_required_config_value(db: Session, config_key: str) -> str:
    """获取必填配置，便于业务接口统一处理配置缺失。"""
    value = get_config_value(db, config_key)
    if value is None:
        raise ConfigNotFoundError(f"系统配置 {config_key} 未配置或未启用")
    return value
