"""11/19 재검토에서 찾은 문제의 재발 방지 테스트."""
import datetime as dt
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.tests.test_core_loop import Q, client, signup_login
from app.tests.test_loop_two import ready_user

BASE = {"password": "Welloop!2345", "name": "테스트", "birth_date": "1974-03-02", "gender": "FEMALE",
        "terms_agreed": True, "privacy_agreed": True}


@pytest.mark.parametrize("patch", [
    {"password": "가나다라마바사아자차카타파하가나다라마바사아자차!1a"},  # 72바이트 초과 (예전엔 500)
    {"password": "12345678"}, {"password": "abcdefgh1"},
    {"birth_date": "2015-01-01"}, {"birth_date": "2090-01-01"}, {"birth_date": "1890-01-01"},
])
def test_signup_rejects_bad_password_and_age(patch):
    r = client.post("/api/v1/auth/signup", json={**BASE, "email": f"bad{abs(hash(str(patch)))}@example.com", **patch})
    assert r.status_code == 400 and r.json()["code"] == "VALIDATION_ERROR"


def test_email_is_case_insensitive_and_long_password_login_fails_cleanly():
    signup_login("case@example.com")
    assert client.post("/api/v1/auth/signup", json={**BASE, "email": "CASE@Example.com"}).status_code == 409
    assert client.post("/api/v1/auth/login", json={"email": " Case@Example.COM ", "password": "Welloop!2345"}).status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": "case@example.com", "password": "가" * 60}).status_code == 401


def test_concurrent_prediction_keeps_three_rows_and_times_have_offset():
    h = signup_login("dup@example.com")
    client.post("/api/v1/consents", json={"consent_type": "HEALTH_DATA", "agreed": True}, headers=h)
    q = client.post("/api/v1/questionnaires", json=Q, headers=h).json()
    assert q["created_at"].endswith("+09:00")
    with ThreadPoolExecutor(4) as pool:
        codes = list(pool.map(lambda _: client.post("/api/v1/predictions", json={"questionnaire_id": q["questionnaire_id"]}, headers=h).status_code, range(4)))
    assert sorted(codes) == [200, 200, 200, 201]
    latest = client.get("/api/v1/predictions/latest", headers=h).json()
    assert len(latest["results"]) == 3 and latest["created_at"].endswith("+09:00")
    assert client.get("/api/v1/predictions", headers=h).json()["total"] == 1


def test_same_day_new_questionnaire_replaces_todays_result():
    h, first = ready_user("redo@example.com")
    q2 = client.post("/api/v1/questionnaires", json={**Q, "waist_size": 110, "activity_days_per_week": 0, "is_recheck": True}, headers=h).json()["questionnaire_id"]
    r = client.post("/api/v1/predictions", json={"questionnaire_id": q2}, headers=h)
    assert r.status_code == 201 and r.json()["results"] != first["results"]
    assert len(r.json()["results"]) == 3
    assert client.get("/api/v1/predictions", headers=h).json()["total"] == 1  # 하루 1회차만 남음
    # 부족한 문진으로 다시 요청하면 400이고, 기존 결과는 지워지지 않음
    q3 = client.post("/api/v1/questionnaires", json={"height": 170}, headers=h).json()["questionnaire_id"]
    assert client.post("/api/v1/predictions", json={"questionnaire_id": q3}, headers=h).status_code == 400
    assert client.get("/api/v1/predictions/latest", headers=h).json()["results"] == r.json()["results"]


def test_future_dates_and_concurrent_saves():
    h, _ = ready_user("fut@example.com")
    future = (dt.date.today() + dt.timedelta(days=30)).isoformat()
    assert client.post("/api/v1/health-logs", json={"log_date": future, "weight": 60}, headers=h).status_code == 400
    assert client.post("/api/v1/checkins", json={"checkin_date": future}, headers=h).status_code == 400
    with ThreadPoolExecutor(4) as pool:
        logs = list(pool.map(lambda _: client.post("/api/v1/health-logs", json={"weight": 60.5}, headers=h).status_code, range(4)))
        checks = list(pool.map(lambda _: client.post("/api/v1/checkins", json={"sleep_hours": 7}, headers=h).status_code, range(4)))
    assert set(logs) <= {200, 201} and set(checks) <= {200, 201}
    logs_now = client.get("/api/v1/health-logs", headers=h).json()
    assert logs_now["total"] == 1
    assert client.patch(f"/api/v1/health-logs/{logs_now['items'][0]['health_log_id']}", json={}, headers=h).status_code == 400
