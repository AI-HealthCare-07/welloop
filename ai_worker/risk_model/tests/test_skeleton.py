"""뼈대 단계 테스트. 원자료 없이 합성 데이터만으로 돌아가요."""
import pytest

from ai_worker.risk_model.config import DATA_SOURCE_SYNTHETIC
from ai_worker.risk_model.data.synthetic import LABEL_COLUMNS, make_synthetic
from ai_worker.risk_model.errors import RiskInputError
from ai_worker.risk_model.spec import load_spec, validate_input
from ai_worker.tasks.risk import predict_risk

VALID = {
    "age": 52, "gender": "FEMALE", "height": 162.0, "weight": 61.0, "waist_size": 82.5,
    "smoking_status": "NEVER", "activity_days_per_week": 2, "sleep_hours": 6.5, "family_dm": "YES",
}


def test_spec_fields_use_erd_enums():
    fields = load_spec()["fields"]
    assert fields["gender"]["values"] == ["MALE", "FEMALE"]
    assert fields["smoking_status"]["values"] == ["NEVER", "FORMER", "CURRENT"]
    assert fields["family_htn"]["values"] == ["YES", "NO", "UNKNOWN"]


def test_synthetic_matches_spec_and_is_marked():
    df = make_synthetic(500)
    spec = load_spec()
    assert set(spec["fields"]) <= set(df.columns)
    assert set(LABEL_COLUMNS.values()) <= set(df.columns)
    assert (df["data_source"] == DATA_SOURCE_SYNTHETIC).all()
    # 합성 데이터에는 입력 금지 필드(혈압·혈당 등)가 없어야 해요
    assert not set(spec["forbidden"]) & set(df.columns)


def test_synthetic_is_reproducible():
    assert make_synthetic(200, seed=1).equals(make_synthetic(200, seed=1))


def test_synthetic_rows_pass_validation():
    df = make_synthetic(50)
    fields = list(load_spec()["fields"])
    for row in df[fields].astype(object).where(df[fields].notna(), None).to_dict("records"):
        validate_input(row)


def test_validate_returns_missing_optional():
    missing = validate_input(VALID)
    assert "veg_freq" in missing and "sleep_hours" not in missing


@pytest.mark.parametrize("patch, field", [
    ({"age": None}, "age"),
    ({"gender": "NO_RESPONSE"}, "gender"),
    ({"waist_size": 500}, "waist_size"),
    ({"activity_days_per_week": 2.5}, "activity_days_per_week"),
    ({"pressure_systolic": 128}, "pressure_systolic"),
    ({"htn_diagnosed": True}, "htn_diagnosed"),
])
def test_validate_rejects_bad_input(patch, field):
    with pytest.raises(RiskInputError) as e:
        validate_input({**VALID, **patch})
    assert field in e.value.errors


def test_predict_risk_validates_then_reports_not_implemented():
    with pytest.raises(RiskInputError):
        predict_risk({**VALID, "age": None})
    with pytest.raises(RiskInputError):
        predict_risk(VALID, diseases=["CANCER"])
    with pytest.raises(NotImplementedError):
        predict_risk(VALID)
