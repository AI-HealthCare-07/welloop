"""모델 저장·불러오기. 모델은 JSON(계수·평균·표준편차)으로 저장해 라이브러리 버전에 묶이지 않아요."""
import json
from functools import lru_cache
from pathlib import Path

from .config import ARTIFACT_DIR, MODEL_VERSION


def version_dir(version: str) -> Path:
    return ARTIFACT_DIR / version


def save(version: str, models: dict, metadata: dict) -> Path:
    d = version_dir(version)
    d.mkdir(parents=True, exist_ok=True)
    (d / "model.json").write_text(json.dumps(models, ensure_ascii=False, indent=1), encoding="utf-8")
    (d / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return d


def available_versions() -> list[str]:
    if not ARTIFACT_DIR.exists():
        return []
    return sorted(p.name for p in ARTIFACT_DIR.iterdir() if (p / "model.json").exists())


def resolve_version(version: str | None = None) -> str:
    """지정 버전 → 환경변수 RISK_MODEL_VERSION → 실제 데이터 모델 중 최신 → 합성 모델 순으로 고릅니다."""
    version = version or MODEL_VERSION
    if version:
        return version
    versions = available_versions()
    if not versions:
        raise FileNotFoundError("학습된 모델이 없어요. `python -m ai_worker.risk_model.train` 을 먼저 실행하세요.")
    real = [v for v in versions if not v.endswith("-synth")]
    return (real or versions)[-1]


@lru_cache(maxsize=4)
def load(version: str) -> tuple[dict, dict]:
    d = version_dir(version)
    models = json.loads((d / "model.json").read_text(encoding="utf-8"))
    metadata = json.loads((d / "metadata.json").read_text(encoding="utf-8"))
    return models, metadata
