from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.mysql import BIGINT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChatCompanionSession(Base):
    __tablename__ = "chat_companion_session"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    session_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("wx_mini_user.id"), nullable=False)
    dify_conversation_id: Mapped[str | None] = mapped_column(String(100))
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    mood: Mapped[str] = mapped_column(String(50), nullable=False)
    event_detail: Mapped[str] = mapped_column(String(1000), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False, server_default="1")
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )


class ChatCompanionMessage(Base):
    __tablename__ = "chat_companion_message"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("chat_companion_session.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    dify_message_id: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
