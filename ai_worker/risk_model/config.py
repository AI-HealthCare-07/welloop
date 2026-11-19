"""경로·시드·모델 버전 설정."""
import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[1]

DATA_DIR = Path(os.environ.get("WELLOOP_DATA_DIR", REPO_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

ARTIFACT_DIR = PACKAGE_DIR / "artifacts"
FEATURE_SPEC_PATH = PACKAGE_DIR / "feature_spec.yaml"

SEED = 42
DISEASES = ("HYPERTENSION", "DIABETES", "DYSLIPIDEMIA")  # ERD Disease_type

# 데이터 출처 표시 (실제·합성 데이터를 섞지 않기 위해 모든 산출물에 기록)
DATA_SOURCE_KNHANES = "KNHANES"
DATA_SOURCE_KAGGLE = "KAGGLE_NHIS"
DATA_SOURCE_SYNTHETIC = "SYNTHETIC"

# 서비스가 사용할 모델 버전. 아직 학습된 모델이 없어요 (단계 2에서 추가).
MODEL_VERSION = os.environ.get("RISK_MODEL_VERSION", "")
