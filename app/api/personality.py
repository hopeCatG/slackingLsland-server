from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.users import get_current_user
from app.core.response import success_response
from app.database import get_db
from app.models.mini_user import WxMiniUser
from app.models.personality import PersonalityAttempt, PersonalityReport
from app.schemas.personality import AnswerRequest
from app.services.personality import (
    answer_question,
    create_attempt,
    current_question,
    get_owned_attempt,
    get_test_or_404,
    serialize_question,
    serialize_report,
    submit_attempt,
)

router = APIRouter(prefix="/personality-tests/worker", tags=["打工人人格测试"])


@router.get("", summary="获取打工人人格测试入口信息")
async def get_worker_test(db: Session = Depends(get_db)) -> dict:
    test = get_test_or_404(db)
    completed_count = db.scalar(select(func.count()).select_from(PersonalityAttempt).where(
        PersonalityAttempt.test_id == test.id,
        PersonalityAttempt.status == 1,
    )) or 0
    return success_response(data={
        "code": test.code,
        "title": test.title,
        "description": test.description,
        "questionCount": test.question_count,
        "completedCount": completed_count,
        "estimatedMinutes": 3,
        "preview": {
            "stem": "下班前 5 分钟收到新消息？",
            "options": ["能做的先推进一小步", "回复收到，明早反馈", "非紧急交给明天的我", "先设提醒，避免明早失忆"],
        },
    })


@router.post("/attempts", summary="创建一次测试会话")
async def start_worker_test(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=64),
    db: Session = Depends(get_db),
    user: WxMiniUser = Depends(get_current_user),
) -> dict:
    attempt = create_attempt(db, user.id, idempotency_key)
    if attempt.status == 1:
        report = db.scalar(select(PersonalityReport).where(PersonalityReport.attempt_id == attempt.id))
        return success_response(data={"attemptId": attempt.attempt_no, "completed": True, "report": serialize_report(report) if report else None})
    question = current_question(db, attempt.id)
    return success_response(data={
        "attemptId": attempt.attempt_no,
        "expiresAt": attempt.expires_at.isoformat(),
        "completed": question is None,
        "question": serialize_question(question) if question else None,
    })


@router.get("/attempts/{attempt_no}", summary="恢复测试进度")
async def get_worker_attempt(
    attempt_no: str,
    db: Session = Depends(get_db),
    user: WxMiniUser = Depends(get_current_user),
) -> dict:
    attempt = get_owned_attempt(db, attempt_no, user.id)
    if attempt.status == 1:
        report = db.scalar(select(PersonalityReport).where(PersonalityReport.attempt_id == attempt.id))
        return success_response(data={"attemptId": attempt.attempt_no, "completed": True, "report": serialize_report(report) if report else None})
    question = current_question(db, attempt.id)
    return success_response(data={
        "attemptId": attempt.attempt_no,
        "expiresAt": attempt.expires_at.isoformat(),
        "completed": False,
        "question": serialize_question(question) if question else None,
    })


@router.put("/attempts/{attempt_no}/answers/{question_id}", summary="提交当前题答案")
async def put_worker_answer(
    attempt_no: str,
    question_id: int,
    payload: AnswerRequest,
    db: Session = Depends(get_db),
    user: WxMiniUser = Depends(get_current_user),
) -> dict:
    attempt = get_owned_attempt(db, attempt_no, user.id)
    next_question = answer_question(db, attempt, question_id, payload.optionId)
    return success_response(data={
        "attemptId": attempt.attempt_no,
        "allAnswered": next_question is None,
        "question": serialize_question(next_question) if next_question else None,
    })


@router.post("/attempts/{attempt_no}/submit", summary="结算并生成测试报告")
async def submit_worker_test(
    attempt_no: str,
    db: Session = Depends(get_db),
    user: WxMiniUser = Depends(get_current_user),
) -> dict:
    attempt = get_owned_attempt(db, attempt_no, user.id)
    report = submit_attempt(db, attempt)
    return success_response(data=serialize_report(report))


@router.get("/reports/{report_no}", summary="获取本人的测试报告")
async def get_worker_report(
    report_no: str,
    db: Session = Depends(get_db),
    user: WxMiniUser = Depends(get_current_user),
) -> dict:
    report = db.scalar(select(PersonalityReport).where(PersonalityReport.report_no == report_no, PersonalityReport.user_id == user.id))
    if report is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    return success_response(data=serialize_report(report))


@router.get("/reports", summary="获取本人的历史报告")
async def list_worker_reports(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user: WxMiniUser = Depends(get_current_user),
) -> dict:
    page = max(1, page)
    page_size = min(50, max(1, page_size))
    query = select(PersonalityReport).where(PersonalityReport.user_id == user.id).order_by(PersonalityReport.created_at.desc())
    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all())
    total = db.scalar(select(func.count()).select_from(PersonalityReport).where(PersonalityReport.user_id == user.id)) or 0
    return success_response(data={"items": [serialize_report(item) for item in items], "page": page, "pageSize": page_size, "total": total})


@router.get("/shared/{share_token}", summary="获取公开分享报告")
async def get_shared_worker_report(share_token: str, db: Session = Depends(get_db)) -> dict:
    report = db.scalar(select(PersonalityReport).where(PersonalityReport.share_token == share_token))
    if report is None:
        raise HTTPException(status_code=404, detail="分享报告不存在或已失效")
    report.view_count += 1
    db.commit()
    return success_response(data={"result": report.report_snapshot_json, "createdAt": report.created_at.isoformat()})
