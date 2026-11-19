"""추론 본체. numpy·난수·외부 호출 없이 계산해서 같은 입력이면 항상 같은 결과가 나와요."""
import math

from . import registry
from .config import DISEASES
from .features import to_vector
from .spec import validate_input

MAX_FACTORS = 3


def _score(model: dict, vector: list[float], answered: set[str]) -> tuple[float, dict[str, float]]:
    z = model["intercept"]
    contrib: dict[str, float] = {}
    for x, fill, mean, scale, coef, src in zip(
        vector, model["impute"], model["mean"], model["scale"], model["coef"], model["source_fields"]
    ):
        missing = math.isnan(x)
        c = coef * ((fill if missing else x) - mean) / scale
        z += c
        if not missing and src in answered:  # 답하지 않은 항목은 '영향 요인'으로 보여 주지 않음
            contrib[src] = contrib.get(src, 0.0) + c
    return 1.0 / (1.0 + math.exp(-z)), contrib


def predict(input_snapshot: dict, diseases: list[str] | None = None, version: str | None = None) -> dict:
    imputed = validate_input(input_snapshot)
    version = registry.resolve_version(version)
    models, metadata = registry.load(version)

    answered = {k for k, v in input_snapshot.items() if v is not None}
    results = []
    for disease in diseases if diseases is not None else DISEASES:
        score, contrib = _score(models[disease], to_vector(input_snapshot, disease), answered)
        raised = sorted((kv for kv in contrib.items() if kv[1] > 0), key=lambda kv: (-kv[1], kv[0]))
        results.append({
            "disease_type": disease,
            "risk_score": round(score, 4),
            "major_factors": [name for name, _ in raised[:MAX_FACTORS]],
        })
    return {
        "model_version": metadata["model_version"],
        "data_source": metadata["data_source"],
        "results": results,
        "imputed_fields": imputed,
    }
