"""화면에 보여 줄 한국어 이름과 오류 문구 (API 공통 에러 응답용)."""
import re

FIELD_LABELS = {
    "email": "이메일", "password": "비밀번호", "name": "이름", "birth_date": "생년월일", "gender": "성별",
    "terms_agreed": "서비스 이용약관 동의", "privacy_agreed": "개인정보 수집·이용 동의", "consent_type": "동의 항목",
    "height": "키", "weight": "몸무게", "waist_size": "허리둘레", "smoking_status": "흡연",
    "drinking_days_per_week": "음주 빈도", "drinks_per_occasion": "1회 음주량",
    "activity_days_per_week": "운동 일수", "activity_minutes_per_day": "하루 운동 시간",
    "strength_days_per_week": "근력운동 일수", "salty_food_freq": "짠 음식 빈도", "sweet_food_freq": "단 음식 빈도",
    "refined_carb_freq": "정제 탄수화물 빈도", "veg_freq": "채소 섭취 빈도", "fruit_freq": "과일 섭취 빈도",
    "breakfast_freq": "아침식사 빈도", "sleep_hours": "수면 시간", "sleep_trouble": "수면 불편",
    "family_htn": "가족력(고혈압)", "family_dm": "가족력(당뇨)", "family_dl": "가족력(이상지질혈증)",
    "exercise_restricted": "운동 제한", "discomfort_symptoms": "불편 증상", "improvement_goal": "개선 목표",
    "menopause_status": "폐경 상태", "log_date": "기록 날짜", "checkin_date": "체크인 날짜",
    "pressure_systolic": "수축기 혈압", "pressure_diastolic": "이완기 혈압", "fasting_glucose": "공복혈당",
    "hba1c": "당화혈색소", "total_cholesterol": "총콜레스테롤", "ldl_cholesterol": "LDL 콜레스테롤",
    "hdl_cholesterol": "HDL 콜레스테롤", "triglycerides": "중성지방", "checkup_date": "검진 받은 날",
    "mood": "기분", "refreshed": "개운함", "stress": "스트레스", "memo": "메모", "medication_taken": "복약 체크",
    "completed_daily_challenge_ids": "완료한 미션", "questionnaire_id": "문진", "changes": "바꿀 항목",
    "category": "카테고리", "title": "제목", "description": "설명", "intensity": "강도", "is_active": "사용 여부",
    "keyword": "키워드", "kind": "종류", "warning_from": "주의 시작값", "high_from": "높음 시작값",
    "page": "페이지", "size": "개수", "period": "기간",
}

# (파이단틱 영문 메시지, 한국어 문구) — {0}은 영문 메시지에서 뽑은 숫자·값이에요
_RULES = [
    (r"greater than or equal to (\S+)", "{0} 이상이어야 해요"),
    (r"less than or equal to (\S+)", "{0} 이하여야 해요"),
    (r"greater than (\S+)", "{0}보다 커야 해요"),
    (r"less than (\S+)", "{0}보다 작아야 해요"),
    (r"at most (\d+) characters", "{0}자 이하로 입력해 주세요"),
    (r"at least (\d+) characters", "{0}자 이상 입력해 주세요"),
    (r"^Field required$", "꼭 입력해야 해요"),
    (r"valid (?:integer|number)", "숫자로 입력해 주세요"),
    (r"valid date", "날짜 형식이 올바르지 않아요"),
    (r"valid boolean", "예·아니오 값이어야 해요"),
    (r"valid list", "목록 형식이 올바르지 않아요"),
    (r"match pattern", "형식이 올바르지 않아요"),
    (r"should be (.+)$", "다음 중 하나여야 해요: {0}"),
]


def _topic(word: str) -> str:
    """받침에 맞는 조사(은/는)를 붙여요."""
    last = word[-1]
    if "가" <= last <= "힣":
        return word + ("은" if (ord(last) - 0xAC00) % 28 else "는")
    return word + "은(는)" if not last.isascii() else word + "는"


def label(field: str) -> str:
    return FIELD_LABELS.get(field, field)


def message(field: str, msg: str) -> str:
    """파이단틱 영문 메시지를 한국어 한 줄로 바꿔요."""
    for pattern, korean in _RULES:
        m = re.search(pattern, msg)
        if m:
            text = korean.format(*(g.replace("'", "").replace(" or ", ", ") for g in (m.groups() or ())))
            return f"{_topic(label(field))} {text}" if field else text
    return f"{label(field)}: {msg}" if field else msg
