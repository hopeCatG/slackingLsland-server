from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, SMALLINT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PersonalityTest(Base):
    __tablename__ = "personality_test"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    question_count: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False, server_default="8")
    daily_limit: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False, server_default="3")
    status: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False, server_default="1")
    current_version_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class PersonalityTestVersion(Base):
    __tablename__ = "personality_test_version"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_test.id"), nullable=False)
    version_no: Mapped[str] = mapped_column(String(32), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(32), nullable=False, server_default="v1")
    status: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False, server_default="0")
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class PersonalityDimension(Base):
    __tablename__ = "personality_dimension"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    sort: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=False, server_default="0")
    status: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class PersonalityQuestion(Base):
    __tablename__ = "personality_question"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    version_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_test_version.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    stem: Mapped[str] = mapped_column(String(500), nullable=False)
    sort: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=False, server_default="0")
    status: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class PersonalityOption(Base):
    __tablename__ = "personality_option"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_question.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(1), nullable=False)
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    dimension_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_dimension.id"), nullable=False)
    score: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False, server_default="0")
    sort: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=False, server_default="0")
    status: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class PersonalityResultProfile(Base):
    __tablename__ = "personality_result_profile"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    version_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_test_version.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_dimension_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_dimension.id"), nullable=False)
    min_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="0")
    max_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="100")
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(150))
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    advice: Mapped[str | None] = mapped_column(String(500))
    tags_json: Mapped[list[str] | None] = mapped_column(JSON)
    illustration_key: Mapped[str | None] = mapped_column(String(100))
    share_title: Mapped[str | None] = mapped_column(String(150))
    status: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class PersonalityAttempt(Base):
    __tablename__ = "personality_attempt"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    attempt_no: Mapped[str] = mapped_column(String(26), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("wx_mini_user.id"), nullable=False)
    test_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_test.id"), nullable=False)
    test_version_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_test_version.id"), nullable=False)
    question_count: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False)
    status: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False, server_default="0")
    idempotency_key: Mapped[str | None] = mapped_column(String(64))
    score_json: Mapped[dict[str, float] | None] = mapped_column(JSON)
    result_profile_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_result_profile.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class PersonalityAttemptQuestion(Base):
    __tablename__ = "personality_attempt_question"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_attempt.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_question.id"), nullable=False)
    position: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False)
    question_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    answered_option_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_option.id"))
    answered_option_code: Mapped[str | None] = mapped_column(String(1))
    answered_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class PersonalityReport(Base):
    __tablename__ = "personality_report"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    report_no: Mapped[str] = mapped_column(String(26), unique=True, nullable=False)
    attempt_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("personality_attempt.id"), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("wx_mini_user.id"), nullable=False)
    result_code: Mapped[str] = mapped_column(String(64), nullable=False)
    report_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    share_token: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    view_count: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
