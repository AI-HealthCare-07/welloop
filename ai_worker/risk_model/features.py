"""input_snapshot → 모델 입력 벡터 (학습·추론 공용, numpy만 사용)."""
import math

# (모델 변수 이름, 설명에 쓸 ERD 컬럼명)
NUMERIC = [
    ("age", "age"), ("bmi", "weight"), ("waist_size", "waist_size"),
    ("drinking_days_per_week", "drinking_days_per_week"), ("drinks_per_occasion", "drinks_per_occasion"),
    ("activity_days_per_week", "activity_days_per_week"), ("activity_minutes_per_day", "activity_minutes_per_day"),
    ("strength_days_per_week", "strength_days_per_week"), ("veg_freq", "veg_freq"), ("fruit_freq", "fruit_freq"),
    ("breakfast_freq", "breakfast_freq"), ("sleep_hours", "sleep_hours"),
]
BINARY = [
    ("gender_male", "gender"), ("smoking_former", "smoking_status"), ("smoking_current", "smoking_status"),
    ("family_yes", None),  # 질환별 가족력 컬럼으로 바뀜 (FAMILY_FIELD)
    ("menopause_peri", "menopause_status"), ("menopause_post", "menopause_status"),
]
FAMILY_FIELD = {"HYPERTENSION": "family_htn", "DIABETES": "family_dm", "DYSLIPIDEMIA": "family_dl"}
FEATURE_NAMES = [n for n, _ in NUMERIC + BINARY]


def source_fields(disease: str) -> list[str]:
    """모델 변수 순서대로, 화면 설명에 쓸 ERD 컬럼명."""
    return [src if src else FAMILY_FIELD[disease] for _, src in NUMERIC + BINARY]


def _num(v):
    if v is None:
        return math.nan
    try:
        f = float(v)
    except (TypeError, ValueError):
        return math.nan
    return f


def to_vector(row: dict, disease: str) -> list[float]:
    """한 사람의 입력을 모델 변수 순서의 숫자 목록으로 바꿔요. 비어 있으면 NaN."""
    h, w = _num(row.get("height")), _num(row.get("weight"))
    bmi = w / (h / 100) ** 2 if h and not math.isnan(h) and not math.isnan(w) else math.nan
    values = {"bmi": bmi}
    for name, _ in NUMERIC:
        if name != "bmi":
            values[name] = _num(row.get(name))
    smoking, meno, fam = row.get("smoking_status"), row.get("menopause_status"), row.get(FAMILY_FIELD[disease])
    values.update({
        "gender_male": 1.0 if row.get("gender") == "MALE" else 0.0,
        "smoking_former": 1.0 if smoking == "FORMER" else 0.0,
        "smoking_current": 1.0 if smoking == "CURRENT" else 0.0,
        "family_yes": 1.0 if fam == "YES" else 0.0,  # NO·UNKNOWN·미응답은 0
        "menopause_peri": 1.0 if meno == "PERI" else 0.0,
        "menopause_post": 1.0 if meno == "POST" else 0.0,
    })
    return [values[n] for n in FEATURE_NAMES]
