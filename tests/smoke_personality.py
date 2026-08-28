"""Run a real-DB smoke test for the worker personality flow, then remove its temporary attempt."""

import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.users import get_current_user  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.mini_user import WxMiniUser  # noqa: E402
from app.models.personality import PersonalityAttempt, PersonalityReport  # noqa: E402


def main() -> None:
    db = SessionLocal()
    user = db.scalar(select(WxMiniUser).where(WxMiniUser.status == 1).limit(1))
    if user is None:
        raise RuntimeError("需要至少一个已启用的 wx_mini_user 才能执行联调")

    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)
    attempt_no = None
    try:
        entry = client.get("/api/v1/personality-tests/worker")
        entry.raise_for_status()
        assert entry.json()["data"]["questionCount"] == 8

        started = client.post(
            "/api/v1/personality-tests/worker/attempts",
            headers={"Idempotency-Key": f"smoke-{time.time_ns()}"},
        )
        started.raise_for_status()
        payload = started.json()["data"]
        attempt_no = payload["attemptId"]
        question = payload["question"]

        while question:
            answered = client.put(
                f"/api/v1/personality-tests/worker/attempts/{attempt_no}/answers/{question['id']}",
                json={"optionId": question["options"][0]["id"]},
            )
            answered.raise_for_status()
            question = answered.json()["data"]["question"]

        submitted = client.post(f"/api/v1/personality-tests/worker/attempts/{attempt_no}/submit")
        submitted.raise_for_status()
        report = submitted.json()["data"]
        assert report["result"]["title"]
        assert len(report["result"]["scores"]) == 4

        owned = client.get(f"/api/v1/personality-tests/worker/reports/{report['reportId']}")
        owned.raise_for_status()
        shared = client.get(f"/api/v1/personality-tests/worker/shared/{report['shareToken']}")
        shared.raise_for_status()
        print(f"smoke ok: 8 answers -> {report['result']['title']} -> owned/shared report")
    finally:
        app.dependency_overrides.clear()
        if attempt_no:
            # The first session may still be on its original REPEATABLE READ snapshot.
            # Re-open it so cleanup can see rows committed by TestClient requests.
            db.rollback()
            db.close()
            db = SessionLocal()
            attempt = db.scalar(select(PersonalityAttempt).where(PersonalityAttempt.attempt_no == attempt_no))
            if attempt:
                db.execute(delete(PersonalityReport).where(PersonalityReport.attempt_id == attempt.id))
                db.delete(attempt)
                db.commit()
        db.close()


if __name__ == "__main__":
    main()
