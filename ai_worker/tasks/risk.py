"""위험 신호 예측 진입점 — 백엔드 서비스 계층이 이 함수만 부르면 돼요.

입출력 계약: docs/planning/WELLOOP_AI모델링_설계_v0.1.md 4·5장

현재 상태(뼈대): 입력 검증까지만 동작합니다. 모델 추론은 단계 2(기준 모델)에서 붙입니다.
"""
from ai_worker.risk_model.config import DISEASES
from ai_worker.risk_model.errors import RiskInputError
from ai_worker.risk_model.spec import validate_input

__all__ = ["predict_risk", "RiskInputError"]


def predict_risk(input_snapshot: dict, diseases: list[str] | None = None) -> dict:
    """문진 + 최신 기록으로 만든 입력 한 건의 질환별 위험 신호를 계산해요.

    input_snapshot: ERD 컬럼명 그대로의 dict (feature_spec.yaml)
    diseases: 계산할 질환 목록. 생략하면 HYPERTENSION · DIABETES · DYSLIPIDEMIA 전부.
              관리 중(is_managed)인 질환은 백엔드가 빼고 넘기면 됩니다.

    반환 (단계 2부터):
        {"model_version": "risk-v0.1", "data_source": "KNHANES",
         "results": [{"disease_type": "DIABETES", "risk_score": 0.62,
                      "major_factors": ["waist_size", "family_dm", "activity_days_per_week"]}],
         "imputed_fields": ["sleep_hours"]}

    위험 단계(risk_level)·종합 점수·is_managed 판단은 백엔드에서 처리합니다.
    """
    targets = list(diseases) if diseases is not None else list(DISEASES)
    unknown = [d for d in targets if d not in DISEASES]
    if unknown:
        raise RiskInputError({"diseases": f"허용값 {list(DISEASES)}"})

    validate_input(input_snapshot)
    raise NotImplementedError("모델 추론은 아직 없어요. 단계 2(기준 모델)에서 구현합니다.")
