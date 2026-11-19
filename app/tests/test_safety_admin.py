"""검진 수치 기준 초과 안내 · 위험 신호 안내 · 관리자."""
import datetime as dt

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.tables import Checkin, User, now
from app.tests.test_core_loop import client, signup_login
from app.tests.test_loop_two import backdate_predictions, ready_user


def admin_headers(email="admin@example.com") -> dict:
    with SessionLocal() as db:
        if not db.query(User).filter_by(email=email).first():
            db.add(User(email=email, password=hash_password("Admin!23456"), name="관리자", birth_date=dt.date(1990, 1, 1),
                        gender="FEMALE", role="ADMIN"))
            db.commit()
    token = client.post("/api/v1/admin/login", json={"email": email, "password": "Admin!23456"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_checkup_exceeded_and_not_used_for_prediction():
    h, before = ready_user("c1@example.com")
    old = (now().date() - dt.timedelta(days=500)).isoformat()
    r = client.post("/api/v1/checkups", json={"checkup_date": old, "pressure_systolic": 150, "fasting_glucose": 100, "hdl_cholesterol": 35}, headers=h)
    assert r.status_code == 201
    assert {e["field"] for e in r.json()["exceeded"]} == {"pressure_systolic", "hdl_cholesterol"}
    assert r.json()["is_stale"] is True and r.json()["guide"]
    assert client.get("/api/v1/checkups/latest", headers=h).json()["checkup_id"] == r.json()["checkup_id"]
    assert client.post("/api/v1/checkups", json={}, headers=h).status_code == 400
    assert "CHECKUP_EXCEEDED" in [a["type"] for a in client.get("/api/v1/safety/alerts", headers=h).json()["items"]]
    # 검진 수치는 예측 입력이 아님: 결과가 그대로
    assert client.get("/api/v1/predictions/latest", headers=h).json()["results"] == before["results"]
    ok = client.post("/api/v1/checkups", json={"pressure_systolic": 118, "pressure_diastolic": 76}, headers=h).json()
    assert ok["exceeded"] == [] and ok["guide"] is None


def test_memo_keyword_gives_crisis_guide_and_low_mood_alert():
    h, _ = ready_user("c2@example.com")
    calm = client.post("/api/v1/checkins", json={"memo": "오늘은 산책해서 기분이 좋았다"}, headers=h).json()
    assert calm["safety_alert"] is None
    r = client.post("/api/v1/checkins", json={"memo": "다 그만두고 사라지고 싶다"}, headers=h).json()
    assert r["safety_alert"]["type"] == "CRISIS" and "109" in r["safety_alert"]["message"]
    assert client.get("/api/v1/safety/alerts", headers=h).json()["items"][0]["type"] == "CRISIS"

    h2, _ = ready_user("c3@example.com")
    with SessionLocal() as db:
        uid = db.query(User).filter_by(email="c3@example.com").one().user_id
        db.add_all(Checkin(user_id=uid, checkin_date=now().date() - dt.timedelta(days=i), mood=1 + i % 2) for i in range(5))
        db.commit()
    assert [a["type"] for a in client.get("/api/v1/safety/alerts", headers=h2).json()["items"]] == ["LOW_MOOD"]


def test_admin_only_and_no_personal_data():
    user_h = signup_login("normal@example.com")
    assert client.get("/api/v1/admin/stats", headers=user_h).status_code == 403
    assert client.post("/api/v1/admin/login", json={"email": "normal@example.com", "password": "Welloop!2345"}).status_code == 403
    assert client.get("/api/v1/admin/stats").status_code == 401
    a = admin_headers()
    stats = client.get("/api/v1/admin/stats", headers=a).json()
    assert stats["total_users"] >= 1 and "email" not in str(stats) and "memo" not in str(stats)


def test_admin_threshold_changes_next_prediction_only():
    a = admin_headers()
    h, first = ready_user("t1@example.com")
    dm = next(r for r in first["results"] if r["disease_type"] == "DIABETES")
    assert client.put("/api/v1/admin/thresholds/DIABETES", json={"warning_from": 0.5, "high_from": 0.4}, headers=a).status_code == 400
    low, high = max(dm["risk_score"] / 3, 0.0001), max(dm["risk_score"] / 2, 0.0002)
    assert client.put("/api/v1/admin/thresholds/DIABETES", json={"warning_from": low, "high_from": high}, headers=a).status_code == 200
    assert client.get("/api/v1/predictions/latest", headers=h).json()["results"] == first["results"]  # 지난 결과는 그대로
    backdate_predictions("t1@example.com", 7)
    client.post("/api/v1/health-logs", json={"weight": 61.5}, headers=h)
    latest = client.get("/api/v1/predictions/latest", headers=h).json()
    assert next(r for r in latest["results"] if r["disease_type"] == "DIABETES")["risk_level"] == "HIGH"
    assert "HIGH_RISK" in [x["type"] for x in client.get("/api/v1/safety/alerts", headers=h).json()["items"]]
    client.put("/api/v1/admin/thresholds/DIABETES", json={"warning_from": 0.15, "high_from": 0.35}, headers=a)  # 다른 테스트에 영향 없게 복구
    assert "경계값 수정" in [g["action"] for g in client.get("/api/v1/admin/stats", headers=a).json()["recent_admin_logs"]]


def test_admin_challenges_and_keywords():
    a = admin_headers()
    c = client.post("/api/v1/admin/challenges", json={"category": "DIET", "title": "물 한 컵 더 마시기"}, headers=a)
    assert c.status_code == 201
    cid = c.json()["challenge_id"]
    assert client.put(f"/api/v1/admin/challenges/{cid}", json={"category": "DIET", "title": "물 두 컵 더", "intensity": "LIGHT"}, headers=a).json()["title"] == "물 두 컵 더"
    assert client.delete(f"/api/v1/admin/challenges/{cid}", headers=a).json()["is_active"] is False  # 삭제 대신 비활성화
    assert client.post("/api/v1/admin/challenges", json={"category": "exercise", "title": "x"}, headers=a).status_code == 400

    k = client.post("/api/v1/admin/safety-keywords", json={"keyword": "끝내고 싶", "kind": "RISK_SIGNAL"}, headers=a)
    assert k.status_code == 201
    assert client.post("/api/v1/admin/safety-keywords", json={"keyword": "끝내고 싶", "kind": "RISK_SIGNAL"}, headers=a).status_code == 409
    h, _ = ready_user("k1@example.com")
    assert client.post("/api/v1/checkins", json={"memo": "이제 다 끝내고 싶어"}, headers=h).json()["safety_alert"]
    assert client.delete(f"/api/v1/admin/safety-keywords/{k.json()['keyword_id']}", headers=a).status_code == 204
    assert client.post("/api/v1/checkins", json={"memo": "이제 다 끝내고 싶어"}, headers=h).json()["safety_alert"] is None
