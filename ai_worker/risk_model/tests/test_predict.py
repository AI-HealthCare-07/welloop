"""추론 테스트. 레포에 들어 있는 합성 모델(risk-v0.0-synth)로 돌아가요."""
import pytest

from ai_worker.risk_model import registry
from ai_worker.risk_model.config import DISEASES
from ai_worker.risk_model.spec import load_spec
from ai_worker.tasks.risk import RiskInputError, predict_risk

VALID = {
    "age": 52, "gender": "FEMALE", "height": 162.0, "weight": 61.0, "waist_size": 82.5,
    "smoking_status": "NEVER", "activity_days_per_week": 2, "sleep_hours": 6.5, "family_dm": "YES",
}


def test_output_contract():
    out = predict_risk(VALID)
    assert set(out) == {"model_version", "data_source", "results", "imputed_fields"}
    assert [r["disease_type"] for r in out["results"]] == list(DISEASES)
    fields = set(load_spec()["fields"])
    for r in out["results"]:
        assert 0.0 <= r["risk_score"] <= 1.0 and round(r["risk_score"], 4) == r["risk_score"]
        assert len(r["major_factors"]) <= 3 and set(r["major_factors"]) <= fields
    assert "veg_freq" in out["imputed_fields"]


def test_synthetic_model_is_labeled():
    out = predict_risk(VALID)
    assert out["model_version"].endswith("-synth") == (out["data_source"] == "SYNTHETIC")


def test_same_input_same_output():
    first = predict_risk(VALID)
    assert all(predict_risk(dict(VALID)) == first for _ in range(100))


def test_diseases_filter_and_errors():
    out = predict_risk(VALID, diseases=["DIABETES"])
    assert [r["disease_type"] for r in out["results"]] == ["DIABETES"]
    with pytest.raises(RiskInputError):
        predict_risk(VALID, diseases=["CANCER"])
    with pytest.raises(RiskInputError):
        predict_risk({**VALID, "age": None})
    with pytest.raises(RiskInputError):
        predict_risk({**VALID, "pressure_systolic": 128})


def test_imputed_field_is_not_a_factor():
    out = predict_risk({k: v for k, v in VALID.items() if k != "sleep_hours"})
    for r in out["results"]:
        assert not set(r["major_factors"]) & set(out["imputed_fields"])


def test_what_if_moves_score():
    """'만약에'는 값을 바꿔 한 번 더 부르면 돼요. 허리둘레가 크면 점수가 올라가야 합니다(합성 모델 기준)."""
    low = predict_risk({**VALID, "waist_size": 75}, ["DIABETES"])["results"][0]["risk_score"]
    high = predict_risk({**VALID, "waist_size": 105}, ["DIABETES"])["results"][0]["risk_score"]
    assert high > low


def test_registry_prefers_real_model(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "ARTIFACT_DIR", tmp_path)
    for v in ["risk-v0.0-synth", "risk-v0.1"]:
        (tmp_path / v).mkdir()
        (tmp_path / v / "model.json").write_text("{}")
    assert registry.resolve_version() == "risk-v0.1"
