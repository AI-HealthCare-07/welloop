"""핵심 루프 ① 가입 → 동의 → 문진 → 예측 → 결과·이력. 임시 DB로 돌아가요."""
import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)
Q = {"height": 162, "weight": 61, "waist_size": 82.5, "smoking_status": "NEVER", "activity_days_per_week": 2,
     "sleep_hours": 6.5, "family_dm": "YES", "family_htn": "UNKNOWN"}


def signup_login(email: str, gender="FEMALE") -> dict:
    r = client.post("/api/v1/auth/signup", json={"email": email, "password": "Welloop!2345", "name": "테스트",
                                                 "birth_date": "1974-03-02", "gender": gender,
                                                 "terms_agreed": True, "privacy_agreed": True})
    assert r.status_code == 201, r.text
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "Welloop!2345"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_signup_rules():
    h = signup_login("a@example.com")
    assert client.get("/api/v1/users/me", headers=h).json()["email"] == "a@example.com"
    dup = client.post("/api/v1/auth/signup", json={"email": "a@example.com", "password": "Welloop!2345", "name": "x",
                                                   "birth_date": "1974-03-02", "gender": "MALE",
                                                   "terms_agreed": True, "privacy_agreed": True})
    assert dup.status_code == 409 and dup.json()["code"] == "EMAIL_DUPLICATED"
    bad = client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "wrong-password"})
    assert bad.status_code == 401
    assert client.get("/api/v1/users/me").status_code == 401


def test_prediction_needs_consent_and_completed_questionnaire():
    h = signup_login("b@example.com")
    qid = client.post("/api/v1/questionnaires", json=Q, headers=h).json()["questionnaire_id"]
    r = client.post("/api/v1/predictions", json={"questionnaire_id": qid}, headers=h)
    assert r.status_code == 409 and r.json()["code"] == "CONSENT_REQUIRED"
    client.post("/api/v1/consents", json={"consent_type": "HEALTH_DATA", "agreed": True}, headers=h)
    draft = client.post("/api/v1/questionnaires", json={**Q, "is_completed": False}, headers=h).json()["questionnaire_id"]
    assert client.post("/api/v1/predictions", json={"questionnaire_id": draft}, headers=h).status_code == 400
    assert client.post("/api/v1/predictions", json={"questionnaire_id": 99999}, headers=h).status_code == 404


def test_undiagnosed_user_gets_risk_view():
    h = signup_login("c@example.com")
    client.post("/api/v1/consents", json={"consent_type": "HEALTH_DATA", "agreed": True}, headers=h)
    qid = client.post("/api/v1/questionnaires", json=Q, headers=h).json()["questionnaire_id"]
    r = client.post("/api/v1/predictions", json={"questionnaire_id": qid}, headers=h)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["view"] == "RISK" and body["managed_diseases"] == []
    assert [x["disease_type"] for x in body["results"]] == ["HYPERTENSION", "DIABETES", "DYSLIPIDEMIA"]
    # 종합 점수 = 가장 높은 단계 질환의 점수 × 100
    basis = next(x for x in body["results"] if x["disease_type"] == body["overall"]["basis_disease_type"])
    assert body["overall"]["score"] == round(basis["risk_score"] * 100) and body["overall"]["grade"] == basis["risk_level"]
    order = {"LOW": 0, "WARNING": 1, "HIGH": 2}
    assert all(order[x["risk_level"]] <= order[basis["risk_level"]] for x in body["results"])
    assert body["is_demo_model"] is True and "의학적 진단이 아니며" in body["disclaimer"]
    assert body["input_sources"]["weight"] == "QUESTIONNAIRE"

    again = client.post("/api/v1/predictions", json={"questionnaire_id": qid}, headers=h)  # 하루 최대 1회
    assert again.status_code == 200 and again.json()["results"] == body["results"]
    assert client.get("/api/v1/predictions/latest", headers=h).json()["prediction_date"] == body["prediction_date"]
    hist = client.get("/api/v1/predictions", headers=h).json()
    assert hist["total"] == 1 and hist["items"][0]["reason"] == "INITIAL" and hist["items"][0]["overall_score"] == body["overall"]["score"]


def test_partly_and_fully_managed_users():
    h = signup_login("d@example.com", "MALE")
    client.post("/api/v1/consents", json={"consent_type": "HEALTH_DATA", "agreed": True}, headers=h)
    qid = client.post("/api/v1/questionnaires", json={**Q, "htn_diagnosed": True}, headers=h).json()["questionnaire_id"]
    body = client.post("/api/v1/predictions", json={"questionnaire_id": qid}, headers=h).json()
    assert body["view"] == "RISK" and body["managed_diseases"] == ["HYPERTENSION"]
    htn = body["results"][0]
    assert htn["is_managed"] and htn["risk_score"] is None and htn["risk_level"] is None
    assert body["overall"]["basis_disease_type"] != "HYPERTENSION"

    h2 = signup_login("e@example.com")
    client.post("/api/v1/consents", json={"consent_type": "HEALTH_DATA", "agreed": True}, headers=h2)
    all_managed = {**Q, "htn_medication": True, "dm_diagnosed": True, "dl_diagnosed": True}
    qid2 = client.post("/api/v1/questionnaires", json=all_managed, headers=h2).json()["questionnaire_id"]
    body2 = client.post("/api/v1/predictions", json={"questionnaire_id": qid2}, headers=h2).json()
    assert body2["view"] == "MANAGEMENT" and body2["overall"] is None and len(body2["managed_diseases"]) == 3


@pytest.mark.parametrize("patch", [{"smoking_status": "NON_SMOKER"}, {"waist_size": 500}, {"family_dm": "maybe"}])
def test_questionnaire_validation(patch):
    h = signup_login(f"v{abs(hash(str(patch)))}@example.com")
    r = client.post("/api/v1/questionnaires", json={**Q, **patch}, headers=h)
    assert r.status_code == 400 and r.json()["code"] == "VALIDATION_ERROR"
