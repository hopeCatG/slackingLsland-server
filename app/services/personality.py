import random
import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.personality import (
    PersonalityAttempt,
    PersonalityAttemptQuestion,
    PersonalityDimension,
    PersonalityOption,
    PersonalityQuestion,
    PersonalityReport,
    PersonalityResultProfile,
    PersonalityTest,
    PersonalityTestVersion,
)

TEST_CODE = "worker_personality"
DISCLAIMER = "仅供娱乐与自我观察，今天的你不等于永远的你。"
DIMENSION_ORDER = ["DRIVE", "BOUNDARY", "CREATIVE", "ENERGY"]

DIMENSIONS = [
    ("DRIVE", "任务驱动", "对目标、节奏与交付的投入度", 10),
    ("BOUNDARY", "边界感", "维护工作与生活边界的倾向", 20),
    ("ENERGY", "能量守恒", "用休息和节奏调节能量的倾向", 30),
    ("CREATIVE", "野路子创造力", "以新方法解决问题的倾向", 40),
]

QUESTIONS = [
    ("Q01", "周一 9:00，你的「开机动画」是？", [
        ("待办已排好，开冲", "DRIVE", 3), ("先看优先级，别急", "BOUNDARY", 3),
        ("咖啡到位再启动", "ENERGY", 3), ("先找个小工具省力", "CREATIVE", 3)]),
    ("Q02", "领导发来「在吗？」你会？", [
        ("秒回并确认要点", "DRIVE", 2), ("回：在，10 分钟后给你答复", "BOUNDARY", 3),
        ("深呼吸，组织语言", "ENERGY", 2), ("在的，雷达已开启——然后问需求", "CREATIVE", 2)]),
    ("Q03", "突然被塞进一个「很急」的需求？", [
        ("拆任务、拉人、开干", "DRIVE", 3), ("先问截止时间和验收标准", "BOUNDARY", 3),
        ("先稳住：我处理一下", "ENERGY", 2), ("找模板、自动化或旧方案抄近路", "CREATIVE", 3)]),
    ("Q04", "下午 3 点电量告急，你的补给方式？", [
        ("列完剩余任务再休息", "DRIVE", 2), ("关 15 分钟通知，专注收尾", "BOUNDARY", 3),
        ("走两分钟，给 CPU 散热", "ENERGY", 3), ("做个表格或脚本让活少一点", "CREATIVE", 3)]),
    ("Q05", "开会 40 分钟后，话题开始绕圈？", [
        ("记下结论和负责人", "DRIVE", 3), ("提议定个结论和下一步", "BOUNDARY", 3),
        ("悄悄喝水，保持人类在线", "ENERGY", 3), ("把散点画成图，试图召唤共识", "CREATIVE", 3)]),
    ("Q06", "同事说「这活怎么又变了」？", [
        ("调整计划，先守住关键交付", "DRIVE", 3), ("说明影响，请对方确认优先级", "BOUNDARY", 3),
        ("先共情一句：确实有点班味", "ENERGY", 2), ("说不定能换个更省事的做法", "CREATIVE", 3)]),
    ("Q07", "下班前 5 分钟收到新消息？", [
        ("能做的先推进一小步", "DRIVE", 2), ("回复收到，明早几点反馈", "BOUNDARY", 3),
        ("非紧急就交给明天的我", "ENERGY", 3), ("先设自动提醒，避免明早失忆", "CREATIVE", 2)]),
    ("Q08", "面对重复性工作，你通常？", [
        ("做成清单，稳定批量完成", "DRIVE", 3), ("划定处理时段，别全天被打断", "BOUNDARY", 3),
        ("交替做轻重任务，避免耗空", "ENERGY", 3), ("邪修一下：想办法自动化", "CREATIVE", 3)]),
    ("Q09", "项目临近截止，群里开始「@所有人」？", [
        ("主动同步进度和风险", "DRIVE", 3), ("明确我负责的范围与依赖", "BOUNDARY", 3),
        ("先做最重要的一件，拒绝慌张", "ENERGY", 3), ("拉出看板，让卡点无处藏身", "CREATIVE", 2)]),
    ("Q10", "你的工位桌面更像？", [
        ("指挥台：资料都在手边", "DRIVE", 2), ("结界：工作物与私人区分开", "BOUNDARY", 3),
        ("补给站：水杯零食充电线齐全", "ENERGY", 3), ("实验室：便利贴和奇怪工具很多", "CREATIVE", 3)]),
    ("Q11", "当你真的搞不定时？", [
        ("提早求助，并带上已尝试方案", "DRIVE", 3), ("说明资源缺口，请协商排期", "BOUNDARY", 3),
        ("允许自己暂停 5 分钟再回来", "ENERGY", 3), ("找跨团队同事换个视角", "CREATIVE", 3)]),
    ("Q12", "你希望同事怎样形容你？", [
        ("交给 TA，我放心", "DRIVE", 3), ("靠谱又有边界", "BOUNDARY", 3),
        ("和 TA 协作不累", "ENERGY", 3), ("总能想出办法", "CREATIVE", 3)]),
]

PROFILES = [
    ("STEADY_ENGINE", "DRIVE", "稳定发动机", "交付到站，请签收", "你不是在上班，你是在把混乱排成队。群里一声「谁来跟」，你已经默默开工。", "给自己也排一个不被打扰的 30 分钟。", ["交付可靠", "行动派", "稳稳接住"], "🚂"),
    ("BOUNDARY_MASTER", "BOUNDARY", "下班结界师", "已离线，但很靠谱", "你不靠 24 小时待机证明认真；你靠清晰优先级把事情办漂亮。", "继续保持同步节奏，边界会让协作更轻松。", ["边界清晰", "拒绝内耗", "沟通到位"], "🪄"),
    ("FISHING_STRATEGIST", "ENERGY", "摸鱼战略家", "能量管理，拒绝空转", "你不是消失，是在给 CPU 散热。该冲时冲，该缓冲时也知道留一口气。", "给摸鱼设一个恢复目的：喝水、走两分钟、再回来收尾。", ["能量管理", "松弛感", "续航在线"], "🐟"),
    ("WILDCARD_SOLVER", "CREATIVE", "邪修解题官", "正路堵车，换条路到达", "别人照 SOP 走，你先看有没有快捷入口；离谱一点，但常常真能成。", "把好点子写成步骤，让野路子也能被团队复用。", ["脑洞在线", "工具达人", "另辟蹊径"], "🛠️"),
    ("CALM_COORDINATOR", "BOUNDARY", "淡定调度员", "事情很多，先别急", "你擅长把「都很急」翻译成「谁最急、先做什么」，混乱到你这里会自动排队。", "遇到模糊需求时，先确认截止时间和验收标准。", ["优先级大师", "情绪稳定", "协作顺滑"], "🧭"),
    ("WARM_TEAMMATE", "ENERGY", "职场发小体质", "有你在，群聊有温度", "你能把「收到」回出人味，也能在别人卡住时递一把梯子。", "先照顾好自己的电量，再持续输出情绪价值。", ["气氛担当", "共情在线", "团队回血"], "🫶"),
]


def _public_id() -> str:
    return secrets.token_hex(16)[:26]


def ensure_default_test_data(db: Session) -> PersonalityTest:
    test = db.scalar(select(PersonalityTest).where(PersonalityTest.code == TEST_CODE))
    if test is None:
        test = PersonalityTest(code=TEST_CODE, title="你的打工人人格是什么？", description="3 分钟生成你的职场隐藏属性", question_count=8, daily_limit=3, status=1)
        db.add(test)
        db.flush()

    dimensions = {item.code: item for item in db.scalars(select(PersonalityDimension)).all()}
    for code, name, description, sort in DIMENSIONS:
        if code not in dimensions:
            dimension = PersonalityDimension(code=code, name=name, description=description, sort=sort, status=1)
            db.add(dimension)
            db.flush()
            dimensions[code] = dimension

    version = None
    if test.current_version_id:
        version = db.get(PersonalityTestVersion, test.current_version_id)
    if version is None:
        version = db.scalar(select(PersonalityTestVersion).where(PersonalityTestVersion.test_id == test.id, PersonalityTestVersion.version_no == "v1.0.0"))
    if version is None:
        version = PersonalityTestVersion(test_id=test.id, version_no="v1.0.0", algorithm_version="v1", status=1, published_at=datetime.now())
        db.add(version)
        db.flush()
    test.current_version_id = version.id
    version.status = 1

    question_count = db.scalar(select(func.count()).select_from(PersonalityQuestion).where(PersonalityQuestion.version_id == version.id)) or 0
    if question_count == 0:
        for index, (code, stem, options) in enumerate(QUESTIONS, start=1):
            question = PersonalityQuestion(version_id=version.id, code=code, stem=stem, sort=index * 10, status=1)
            db.add(question)
            db.flush()
            for option_index, (content, dimension_code, score) in enumerate(options):
                db.add(PersonalityOption(
                    question_id=question.id, code=chr(65 + option_index), content=content,
                    dimension_id=dimensions[dimension_code].id, score=score, sort=(option_index + 1) * 10, status=1,
                ))

    profile_count = db.scalar(select(func.count()).select_from(PersonalityResultProfile).where(PersonalityResultProfile.version_id == version.id)) or 0
    if profile_count == 0:
        for code, dimension_code, title, subtitle, narrative, advice, tags, emoji in PROFILES:
            db.add(PersonalityResultProfile(
                version_id=version.id, code=code, primary_dimension_id=dimensions[dimension_code].id,
                min_score=0, max_score=100, title=title, subtitle=subtitle, narrative=narrative,
                advice=advice, tags_json=tags, illustration_key=emoji, share_title=f"我的打工人人格是「{title}」", status=1,
            ))
    db.commit()
    db.refresh(test)
    return test


def get_test_or_404(db: Session) -> PersonalityTest:
    test = ensure_default_test_data(db)
    if test.status != 1 or not test.current_version_id:
        raise HTTPException(status_code=404, detail="测试暂未开放")
    return test


def serialize_question(row: PersonalityAttemptQuestion) -> dict:
    snapshot = row.question_snapshot_json
    return {
        "id": row.question_id,
        "position": row.position,
        "total": snapshot["total"],
        "stem": snapshot["stem"],
        "options": [{"id": option["id"], "code": option["displayCode"], "content": option["content"]} for option in snapshot["options"]],
    }


def current_question(db: Session, attempt_id: int) -> PersonalityAttemptQuestion | None:
    return db.scalar(select(PersonalityAttemptQuestion).where(
        PersonalityAttemptQuestion.attempt_id == attempt_id,
        PersonalityAttemptQuestion.answered_option_id.is_(None),
    ).order_by(PersonalityAttemptQuestion.position).limit(1))


def create_attempt(db: Session, user_id: int, idempotency_key: str | None) -> PersonalityAttempt:
    test = get_test_or_404(db)
    now = datetime.now()
    if idempotency_key:
        existing = db.scalar(select(PersonalityAttempt).where(PersonalityAttempt.user_id == user_id, PersonalityAttempt.idempotency_key == idempotency_key))
        if existing:
            return existing

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    completed_today = db.scalar(select(func.count()).select_from(PersonalityAttempt).where(
        PersonalityAttempt.user_id == user_id,
        PersonalityAttempt.test_id == test.id,
        PersonalityAttempt.status == 1,
        PersonalityAttempt.submitted_at >= day_start,
    )) or 0
    if test.daily_limit and completed_today >= test.daily_limit:
        raise HTTPException(status_code=429, detail="今天已经测了 3 次啦，明天再来看看人格有没有更新")

    questions = list(db.scalars(select(PersonalityQuestion).where(
        PersonalityQuestion.version_id == test.current_version_id,
        PersonalityQuestion.status == 1,
    )).all())
    if len(questions) < test.question_count:
        raise HTTPException(status_code=503, detail="题库正在补充中，请稍后再试")
    selected = random.sample(questions, test.question_count)
    attempt = PersonalityAttempt(
        attempt_no=_public_id(), user_id=user_id, test_id=test.id, test_version_id=test.current_version_id,
        question_count=test.question_count, status=0, idempotency_key=idempotency_key,
        expires_at=now + timedelta(minutes=30),
    )
    db.add(attempt)
    db.flush()

    dimension_codes = {item.id: item.code for item in db.scalars(select(PersonalityDimension)).all()}
    for position, question in enumerate(selected, start=1):
        options = list(db.scalars(select(PersonalityOption).where(PersonalityOption.question_id == question.id, PersonalityOption.status == 1)).all())
        random.shuffle(options)
        snapshot_options = []
        for index, option in enumerate(options):
            snapshot_options.append({
                "id": option.id, "sourceCode": option.code, "displayCode": chr(65 + index),
                "content": option.content, "dimension": dimension_codes[option.dimension_id], "score": option.score,
            })
        db.add(PersonalityAttemptQuestion(
            attempt_id=attempt.id, question_id=question.id, position=position,
            question_snapshot_json={"code": question.code, "stem": question.stem, "total": test.question_count, "options": snapshot_options},
        ))
    db.commit()
    db.refresh(attempt)
    return attempt


def get_owned_attempt(db: Session, attempt_no: str, user_id: int) -> PersonalityAttempt:
    attempt = db.scalar(select(PersonalityAttempt).where(PersonalityAttempt.attempt_no == attempt_no, PersonalityAttempt.user_id == user_id))
    if attempt is None:
        raise HTTPException(status_code=404, detail="测试记录不存在")
    if attempt.status == 0 and attempt.expires_at < datetime.now():
        attempt.status = 2
        db.commit()
        raise HTTPException(status_code=410, detail="本次测试已过期，请重新开始")
    return attempt


def answer_question(db: Session, attempt: PersonalityAttempt, question_id: int, option_id: int) -> PersonalityAttemptQuestion | None:
    if attempt.status != 0:
        raise HTTPException(status_code=409, detail="本次测试已经结束")
    current = current_question(db, attempt.id)
    if current is None:
        return None
    if current.question_id != question_id:
        raise HTTPException(status_code=409, detail="请按顺序完成题目")
    selected = next((item for item in current.question_snapshot_json["options"] if item["id"] == option_id), None)
    if selected is None:
        raise HTTPException(status_code=422, detail="选项不属于当前题目")
    current.answered_option_id = option_id
    current.answered_option_code = selected["displayCode"]
    current.answered_at = datetime.now()
    db.commit()
    return current_question(db, attempt.id)


def _choose_profile(profiles: list[PersonalityResultProfile], ranking: list[tuple[str, float]]) -> PersonalityResultProfile:
    primary, primary_score = ranking[0]
    secondary, secondary_score = ranking[1]
    special_code = None
    if primary == "BOUNDARY" and secondary == "ENERGY" and primary_score - secondary_score <= 8:
        special_code = "CALM_COORDINATOR"
    elif primary == "ENERGY" and secondary == "BOUNDARY" and primary_score - secondary_score <= 8:
        special_code = "WARM_TEAMMATE"
    if special_code:
        special = next((item for item in profiles if item.code == special_code), None)
        if special:
            return special
    default_codes = {"DRIVE": "STEADY_ENGINE", "BOUNDARY": "BOUNDARY_MASTER", "ENERGY": "FISHING_STRATEGIST", "CREATIVE": "WILDCARD_SOLVER"}
    profile = next((item for item in profiles if item.code == default_codes[primary] and float(item.min_score) <= primary_score <= float(item.max_score)), None)
    if profile is None:
        raise HTTPException(status_code=503, detail="结果模板配置不完整")
    return profile


def submit_attempt(db: Session, attempt: PersonalityAttempt) -> PersonalityReport:
    existing = db.scalar(select(PersonalityReport).where(PersonalityReport.attempt_id == attempt.id))
    if existing:
        return existing
    if attempt.status != 0:
        raise HTTPException(status_code=409, detail="本次测试无法结算")
    answers = list(db.scalars(select(PersonalityAttemptQuestion).where(PersonalityAttemptQuestion.attempt_id == attempt.id).order_by(PersonalityAttemptQuestion.position)).all())
    if len(answers) != attempt.question_count or any(item.answered_option_id is None for item in answers):
        raise HTTPException(status_code=422, detail="请完成全部题目后再查看结果")

    raw_scores = {code: 0 for code in DIMENSION_ORDER}
    for answer in answers:
        selected = next(item for item in answer.question_snapshot_json["options"] if item["id"] == answer.answered_option_id)
        raw_scores[selected["dimension"]] += int(selected["score"])
    total = sum(raw_scores.values()) or 1
    normalized = {code: round(score / total * 100, 2) for code, score in raw_scores.items()}
    order_index = {code: index for index, code in enumerate(DIMENSION_ORDER)}
    ranking = sorted(normalized.items(), key=lambda item: (-item[1], order_index[item[0]]))
    profiles = list(db.scalars(select(PersonalityResultProfile).where(PersonalityResultProfile.version_id == attempt.test_version_id, PersonalityResultProfile.status == 1)).all())
    profile = _choose_profile(profiles, ranking)
    dimensions = {item.code: item.name for item in db.scalars(select(PersonalityDimension)).all()}
    match_percent = min(99, max(72, round(72 + (ranking[0][1] - 25) * 0.8)))
    snapshot = {
        "title": profile.title,
        "subtitle": profile.subtitle,
        "emoji": profile.illustration_key or "✨",
        "matchPercent": match_percent,
        "dominantTraits": [dimensions[ranking[0][0]], dimensions[ranking[1][0]]],
        "narrative": profile.narrative,
        "advice": profile.advice,
        "tags": profile.tags_json or [],
        "scores": normalized,
        "disclaimer": DISCLAIMER,
        "shareTitle": profile.share_title,
    }
    report = PersonalityReport(
        report_no=_public_id(), attempt_id=attempt.id, user_id=attempt.user_id, result_code=profile.code,
        report_snapshot_json=snapshot, share_token=secrets.token_hex(16),
    )
    attempt.status = 1
    attempt.score_json = normalized
    attempt.result_profile_id = profile.id
    attempt.submitted_at = datetime.now()
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def serialize_report(report: PersonalityReport) -> dict:
    return {"reportId": report.report_no, "shareToken": report.share_token, "result": report.report_snapshot_json, "createdAt": report.created_at.isoformat()}
