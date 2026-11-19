"""feature_spec.yaml 읽기와 input_snapshot 검증."""
from functools import lru_cache

import yaml

from .config import FEATURE_SPEC_PATH
from .errors import RiskInputError


@lru_cache(maxsize=1)
def load_spec() -> dict:
    with open(FEATURE_SPEC_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_input(input_snapshot: dict) -> list[str]:
    """입력 계약에 맞는지 확인하고, 비어 있는 선택 필드 이름 목록을 돌려줘요.

    필수 누락·타입·범위·허용값 오류와 금지 필드가 있으면 RiskInputError.
    계약에 없는 그 밖의 키는 무시합니다.
    """
    spec = load_spec()
    errors: dict[str, str] = {}
    missing_optional: list[str] = []

    for name in spec.get("forbidden", []):
        if input_snapshot.get(name) is not None:
            errors[name] = "예측 입력에 넣을 수 없는 값"

    for name, rule in spec["fields"].items():
        value = input_snapshot.get(name)
        if value is None:
            if rule.get("required"):
                errors[name] = "필수값 누락"
            else:
                missing_optional.append(name)
            continue

        kind = rule["type"]
        if kind == "enum":
            if value not in rule["values"]:
                errors[name] = f"허용값 {rule['values']}"
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors[name] = "숫자여야 함"
            continue
        if kind == "int" and int(value) != value:
            errors[name] = "정수여야 함"
            continue
        if value < rule["min"] or value > rule["max"]:
            errors[name] = f"범위 {rule['min']}~{rule['max']}"

    if errors:
        raise RiskInputError(errors)
    return missing_optional
