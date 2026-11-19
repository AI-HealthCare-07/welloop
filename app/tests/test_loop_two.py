"""핵심 루프 ② 미션 → 체크인 → 기록 → 대시보드 → 재계산 · 만약에 · 관리 평가."""
import datetime as dt

from app.core.db import SessionLocal
from app.models.tables import Checkin, RiskPrediction, User, now
from app.services import prediction_service as pred
from app.tests.test_core_loop import Q, client, signup_login


def ready_user(email: str, **q) -> tuple[dict, dict]:
    h = signup_login(email)
    client.post("/api/v1/consents", json={"consent_type": "HEALTH_DATA", "agreed": True}, headers=h)
    qid = client.post("/api/v1/questionnaires", json={**Q, **q}, headers=h).json()["questionnaire_id"]
    return h, client.post("/api/v1/predictions", json={"questionnaire_id": qid}, headers=h).json()


def backdate_predictions(email: str, days: int) -> None:
    """'하루 최대 1회' 때문에, 테스트에서는 오늘 예측을 과거로 옮겨 다음 계산이 가능하게 해요."""
    with SessionLocal() as db:
        uid = db.query(User).filter_by(email=email).one().user_id
        for r in db.query(RiskPrediction).filter_by(user_id=uid, prediction_date=now().date()):
            r.prediction_date -= dt.timedelta(days=days)
        db.commit()


def test_missions_checkin_and_coach():
    h, _ = ready_user("m1@example.com")
    today = client.get("/api/v1/challenges/today", headers=h).json()
    assert 1 <= len(today["missions"]) <= 3
    assert today["recommended_categories"][0]["category"] == "ACTIVITY"  # 주 2일 → 신체활동 먼저
    ids = [m["daily_challenge_id"] for m in today["missions"]]
    assert client.get("/api/v1/challenges/today", headers=h).json()["missions"] == today["missions"]  # 다시 불러도 같음

    r = client.post("/api/v1/checkins", json={"completed_daily_challenge_ids": ids[:1], "sleep_hours": 7, "mood": 4}, headers=h)
    assert r.status_code == 201 and r.json()["completion_rate"] == round(1 / len(ids), 2) and r.json()["streak_days"] == 1
    again = client.post("/api/v1/checkins", json={"completed_daily_challenge_ids": ids}, headers=h)
    assert again.status_code == 200 and again.json()["completion_rate"] == 1.0  # 같은 날은 덮어쓰기
    bad = client.post("/api/v1/checkins", json={"completed_daily_challenge_ids": [999999]}, headers=h)
    assert bad.status_code == 400  # 배정되지 않은 미션

    c1 = client.get("/api/v1/coach/today", headers=h).json()
    assert c1["source"] == "TEMPLATE" and c1 == client.get("/api/v1/coach/today", headers=h).json()


def test_health_log_recalculates_once_a_day():
    h, first = ready_user("r1@example.com")
    same_day = client.post("/api/v1/health-logs", json={"weight": 60.0}, headers=h)
    assert same_day.status_code == 201 and same_day.json()["recalculated"] is False  # 오늘 이미 계산함

    backdate_predictions("r1@example.com", 7)
    r = client.post("/api/v1/health-logs", json={"weight": 75.0, "waist_size": 95.0}, headers=h)
    assert r.status_code == 200 and r.json()["recalculated"] is True
    latest = client.get("/api/v1/predictions/latest", headers=h).json()
    assert latest["input_sources"]["weight"] == "HEALTH_LOG" and latest["input_sources"]["waist_size"] == "HEALTH_LOG"
    hist = client.get("/api/v1/predictions", headers=h).json()
    assert [i["reason"] for i in hist["items"]] == ["HEALTH_LOG", "INITIAL"]

    bp_only = client.post("/api/v1/health-logs", json={"pressure_systolic": 128, "pressure_diastolic": 82}, headers=h)
    assert bp_only.json()["recalculated"] is False  # 혈압은 예측 입력이 아님
    assert client.post("/api/v1/health-logs", json={"pressure_systolic": 128}, headers=h).status_code == 400
    assert client.post("/api/v1/health-logs", json={}, headers=h).status_code == 400

    dash = client.get("/api/v1/dashboard", headers=h).json()
    assert len(dash["risk_score_trend"]["points"]) == 2
    assert {t["metric"] for t in dash["health_trends"]} == {"weight", "waist_size", "pressure_systolic"}
    log_id = client.get("/api/v1/health-logs", headers=h).json()["items"][0]["health_log_id"]
    assert client.patch(f"/api/v1/health-logs/{log_id}", json={"weight": 74.0}, headers=h).json()["weight"] == 74.0
    other, _ = ready_user("r2@example.com")
    assert client.delete(f"/api/v1/health-logs/{log_id}", headers=other).status_code == 403
    assert client.delete(f"/api/v1/health-logs/{log_id}", headers=h).status_code == 204


def test_empty_dashboard_has_no_fake_data():
    h = signup_login("empty@example.com")
    dash = client.get("/api/v1/dashboard", headers=h).json()
    assert dash["risk_score_trend"]["points"] == [] and dash["health_trends"] == []
    assert client.get("/api/v1/predictions/latest", headers=h).status_code == 404


def test_sleep_rule_seven_of_fourteen_days():
    h, first = ready_user("s1@example.com")
    assert first["input_sources"]["sleep_hours"] == "QUESTIONNAIRE"
    backdate_predictions("s1@example.com", 20)
    with SessionLocal() as db:
        user = db.query(User).filter_by(email="s1@example.com").one()
        for i in range(6):
            db.add(Checkin(user_id=user.user_id, checkin_date=now().date() - dt.timedelta(days=i), sleep_hours=8.0))
        db.commit()
        assert pred.weekly_sleep_recalculation(db, user) is False  # 6일뿐 → 문진 값 유지 → 차이 없음
        db.add(Checkin(user_id=user.user_id, checkin_date=now().date() - dt.timedelta(days=6), sleep_hours=8.0))
        db.commit()
        assert pred.weekly_sleep_recalculation(db, user) is True  # 7일 평균 8.0 vs 문진 6.5
    latest = client.get("/api/v1/predictions/latest", headers=h).json()
    assert latest["input_sources"]["sleep_hours"] == "CHECKIN_14D"
    assert client.get("/api/v1/predictions", headers=h).json()["items"][0]["reason"] == "SLEEP_CHECKIN"


def test_simulate_is_not_saved():
    h, first = ready_user("w1@example.com")
    r = client.post("/api/v1/predictions/simulate", json={"changes": {"waist_size": 110, "activity_days_per_week": 0}}, headers=h)
    assert r.status_code == 200 and r.json()["is_saved"] is False
    assert r.json()["overall"]["simulated"] >= r.json()["overall"]["current"]
    assert r.json()["changes"][0] == {"code": "waist_size", "label": "허리둘레", "unit": "cm", "current": 82.5, "assumed": 110}
    assert client.post("/api/v1/predictions/simulate", json={"changes": {"age": 30}}, headers=h).status_code == 400
    assert client.post("/api/v1/predictions/simulate", json={"changes": {"waist_size": 999}}, headers=h).status_code == 400
    assert client.get("/api/v1/predictions", headers=h).json()["total"] == 1


def test_management_summary_for_managed_user():
    h, body = ready_user("g1@example.com", htn_diagnosed=True, htn_medication=True)
    assert body["managed_diseases"] == ["HYPERTENSION"]
    ids = [m["daily_challenge_id"] for m in client.get("/api/v1/challenges/today", headers=h).json()["missions"]]
    client.post("/api/v1/checkins", json={"completed_daily_challenge_ids": ids[:1], "medication_taken": True}, headers=h)
    client.post("/api/v1/health-logs", json={"pressure_systolic": 128, "pressure_diastolic": 82}, headers=h)
    s = client.get("/api/v1/management/summary", headers=h).json()
    assert s["completion"] == {"rate": round(1 / len(ids), 2), "planned_count": len(ids), "completed_count": 1}
    item = s["managed_items"][0]
    assert item["disease_type"] == "HYPERTENSION" and item["latest_log"]["pressure_systolic"] == 128
    assert item["medication_check"] == {"checked_days": 1, "total_days": 7}
    h2, _ = ready_user("g2@example.com")
    assert client.get("/api/v1/management/summary", headers=h2).status_code == 404


def test_concurrent_home_requests_do_not_fail():
    """홈 화면은 코치·미션을 동시에 불러요. 둘 다 미션을 배정하려 해도 오류가 나면 안 됩니다."""
    from concurrent.futures import ThreadPoolExecutor

    h, _ = ready_user("race@example.com")
    with ThreadPoolExecutor(6) as pool:
        codes = list(pool.map(lambda p: client.get(p, headers=h).status_code,
                              ["/api/v1/coach/today", "/api/v1/challenges/today"] * 3))
    assert codes == [200] * 6
    assert len(client.get("/api/v1/challenges/today", headers=h).json()["missions"]) <= 3
