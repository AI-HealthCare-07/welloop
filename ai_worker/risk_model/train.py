"""기준 모델 학습: 질환별 로지스틱 회귀.

실행 (레포 루트):
  python -m ai_worker.risk_model.train --data data/processed/synthetic_cohort.parquet --version risk-v0.0-synth

- 결측은 학습 데이터 중앙값으로 채우고 표준화합니다 (학습 데이터에서만 맞춤).
- 검증은 층화 분할 25% 홀드아웃. 국건영 실제 데이터에서는 연도 분할(2024 테스트)로 바꿉니다 (단계 1 이후).
- 합성 데이터로 만든 모델의 지표에는 의미가 없어요. 버전은 반드시 '-synth'로 끝나야 합니다.
"""
import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from . import registry
from .config import DATA_SOURCE_SYNTHETIC, DISEASES, SEED
from .data.synthetic import LABEL_COLUMNS
from .features import FEATURE_NAMES, source_fields, to_vector


def _matrix(df: pd.DataFrame, disease: str) -> np.ndarray:
    rows = df.astype(object).where(df.notna(), None).to_dict("records")
    return np.array([to_vector(r, disease) for r in rows], dtype=float)


def train_one(df: pd.DataFrame, disease: str) -> tuple[dict, dict]:
    X, y = _matrix(df, disease), df[LABEL_COLUMNS[disease]].to_numpy()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEED)

    median = np.nanmedian(X_tr, axis=0)
    fill = lambda A: np.where(np.isnan(A), median, A)  # noqa: E731
    X_tr_f, X_te_f = fill(X_tr), fill(X_te)
    mean, scale = X_tr_f.mean(axis=0), X_tr_f.std(axis=0)
    scale[scale == 0] = 1.0

    clf = LogisticRegression(C=1.0, max_iter=1000).fit((X_tr_f - mean) / scale, y_tr)
    p = clf.predict_proba((X_te_f - mean) / scale)[:, 1]

    model = {
        "type": "logistic_regression", "features": FEATURE_NAMES, "source_fields": source_fields(disease),
        "impute": median.round(6).tolist(), "mean": mean.round(6).tolist(), "scale": scale.round(6).tolist(),
        "coef": clf.coef_[0].round(6).tolist(), "intercept": round(float(clf.intercept_[0]), 6),
    }
    metrics = {
        "n_train": int(len(y_tr)), "n_test": int(len(y_te)), "positive_rate": round(float(y.mean()), 4),
        "auroc": round(float(roc_auc_score(y_te, p)), 4), "auprc": round(float(average_precision_score(y_te, p)), 4),
        "brier": round(float(brier_score_loss(y_te, p)), 4),
    }
    return model, metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="기준 모델(로지스틱 회귀) 학습")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    df = pd.read_parquet(args.data)
    sources = sorted(df["data_source"].unique())
    if len(sources) != 1:
        raise SystemExit(f"데이터 출처가 섞여 있어요: {sources}")
    if (sources[0] == DATA_SOURCE_SYNTHETIC) != args.version.endswith("-synth"):
        raise SystemExit("합성 데이터 모델은 버전이 '-synth'로 끝나야 하고, 실제 데이터 모델은 그러면 안 돼요.")

    models, metrics = {}, {}
    for disease in DISEASES:
        models[disease], metrics[disease] = train_one(df, disease)
        print(disease, metrics[disease])

    metadata = {
        "model_version": args.version, "data_source": sources[0], "trained_on": dt.date.today().isoformat(),
        "model_type": "logistic_regression (기준 모델)", "split": "층화 홀드아웃 25%", "metrics": metrics,
        "note": "합성 데이터 모델: 지표·점수에 의미 없음. 연동·화면 개발용." if sources[0] == DATA_SOURCE_SYNTHETIC else "",
    }
    print("저장:", registry.save(args.version, models, metadata))


if __name__ == "__main__":
    main()
