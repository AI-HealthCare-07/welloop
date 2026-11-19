"""합성 데이터 생성 (개발·테스트 전용).

실제 사람의 데이터가 아니에요. 분포와 관계는 코드로 지어낸 값이라
이 데이터로 만든 모델의 성능·점수에는 의미가 없습니다.
- 모든 행에 data_source = "SYNTHETIC"
- 이 데이터로 학습한 모델 버전에는 "-synth"를 붙입니다.

실행: python -m ai_worker.risk_model.data.synthetic --n 3000 --out data/processed/synthetic_cohort.parquet
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import DATA_SOURCE_SYNTHETIC, SEED

LABEL_COLUMNS = {"HYPERTENSION": "label_htn", "DIABETES": "label_dm", "DYSLIPIDEMIA": "label_dl"}


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def make_synthetic(n: int = 3000, seed: int = SEED) -> pd.DataFrame:
    """feature_spec.yaml과 같은 컬럼 + 질환별 라벨 3개를 가진 합성 데이터."""
    rng = np.random.default_rng(seed)

    age = rng.integers(45, 80, n)
    gender = rng.choice(["MALE", "FEMALE"], n)
    male = gender == "MALE"
    height = np.where(male, rng.normal(168, 6, n), rng.normal(156, 6, n)).clip(135, 195).round(1)
    bmi = rng.normal(24.2, 3.2, n).clip(16, 40)
    weight = (bmi * (height / 100) ** 2).round(1)
    waist = (np.where(male, 60, 55) + bmi * 1.1 + rng.normal(0, 4, n)).clip(55, 130).round(1)

    smoking = np.where(
        male,
        rng.choice(["NEVER", "FORMER", "CURRENT"], n, p=[0.25, 0.45, 0.30]),
        rng.choice(["NEVER", "FORMER", "CURRENT"], n, p=[0.90, 0.05, 0.05]),
    )
    drinking_days = rng.choice(8, n, p=[0.40, 0.22, 0.14, 0.09, 0.06, 0.04, 0.03, 0.02])
    drinks = np.where(drinking_days == 0, 0, rng.integers(1, 10, n))
    activity_days = rng.integers(0, 8, n)
    activity_minutes = np.where(activity_days == 0, 0, rng.choice([10, 20, 30, 40, 60, 90], n))
    strength_days = rng.choice(8, n, p=[0.60, 0.10, 0.10, 0.08, 0.05, 0.04, 0.02, 0.01])
    veg = rng.integers(0, 22, n)
    fruit = rng.integers(0, 15, n)
    breakfast = rng.choice(8, n, p=[0.10, 0.03, 0.04, 0.05, 0.05, 0.08, 0.10, 0.55])
    sleep = rng.normal(6.7, 1.2, n).clip(3, 11).round(1)
    family = lambda p: rng.choice(["YES", "NO", "UNKNOWN"], n, p=[p, 0.85 - p, 0.15])  # noqa: E731
    family_htn, family_dm, family_dl = family(0.30), family(0.20), family(0.10)
    menopause = np.where(
        male, None, np.where(age >= 55, "POST", rng.choice(["PRE", "PERI", "POST"], n, p=[0.25, 0.30, 0.45]))
    )

    df = pd.DataFrame({
        "age": age, "gender": gender, "height": height, "weight": weight, "waist_size": waist,
        "smoking_status": smoking, "drinking_days_per_week": drinking_days, "drinks_per_occasion": drinks,
        "activity_days_per_week": activity_days, "activity_minutes_per_day": activity_minutes,
        "strength_days_per_week": strength_days, "veg_freq": veg, "fruit_freq": fruit,
        "breakfast_freq": breakfast, "sleep_hours": sleep,
        "family_htn": family_htn, "family_dm": family_dm, "family_dl": family_dl,
        "menopause_status": menopause,
    })

    # 지어낸 관계식으로 라벨 생성 (양성 비율만 대략 맞춤: 14% / 6% / 33%)
    base = 0.04 * (age - 60) + 0.05 * (waist - 85) + 0.3 * (smoking == "CURRENT") - 0.06 * activity_days
    df["label_htn"] = rng.binomial(1, _sigmoid(-2.0 + base + 0.5 * (family_htn == "YES") + 0.08 * drinking_days))
    df["label_dm"] = rng.binomial(1, _sigmoid(-3.1 + base + 0.7 * (family_dm == "YES")))
    df["label_dl"] = rng.binomial(1, _sigmoid(-0.8 + 0.6 * base + 0.4 * (family_dl == "YES")))
    df["data_source"] = DATA_SOURCE_SYNTHETIC

    # 선택 문항 미응답 흉내 (약 5%)
    for col in ["sleep_hours", "veg_freq", "fruit_freq", "strength_days_per_week"]:
        df[col] = df[col].astype("float").mask(rng.random(n) < 0.05)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="합성 데이터 생성 (개발·테스트 전용)")
    parser.add_argument("--n", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    df = make_synthetic(args.n, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)
    rates = {d: round(float(df[c].mean()), 3) for d, c in LABEL_COLUMNS.items()}
    print(f"합성 데이터 {len(df)}행 저장: {args.out} / 양성 비율 {rates} / data_source=SYNTHETIC")


if __name__ == "__main__":
    main()
