"""04 구역: 추천 카테고리 · 오늘의 미션 · 체크인. 05: 오늘의 코치 메시지(고정 문구, LLM 연결 자리)."""
import datetime as dt
import os

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import api_error
from app.models.tables import Challenge, Checkin, CoachMessage, DailyChallenge, User, now
from app.services import prediction_service as pred

CATEGORY_LABELS = {"DIET": "식습관", "ACTIVITY": "신체활동", "SLEEP_REST": "수면·휴식", "SMOKE_DRINK": "금연·절주"}
SEED_CHALLENGES = [
    ("DIET", "국물은 반만 먹기", "국·찌개 국물을 반만 드셔 보세요.", "LIGHT"),
    ("DIET", "단 음료 대신 물 마시기", "오늘 하루 단 음료를 물이나 차로 바꿔 보세요.", "LIGHT"),
    ("DIET", "채소 반찬 한 가지 더", "한 끼에 채소 반찬을 하나 더 올려 보세요.", "LIGHT"),
    ("ACTIVITY", "식후 10분 걷기", "식사 후 10분만 가볍게 걸어 보세요.", "LIGHT"),
    ("ACTIVITY", "계단 두 층 오르기", "엘리베이터 대신 계단을 두 층만 이용해 보세요.", "MODERATE"),
    ("ACTIVITY", "빠르게 걷기 30분", "숨이 조금 찰 정도로 30분 걸어 보세요.", "HARD"),
    ("SLEEP_REST", "잠들기 1시간 전 화면 끄기", "잠자리에 들기 1시간 전에는 휴대폰을 내려놓아 보세요.", "LIGHT"),
    ("SLEEP_REST", "1분 호흡하기", "편하게 앉아 4초 들이쉬고 6초 내쉬기를 1분간 해 보세요.", "LIGHT"),
    ("SLEEP_REST", "같은 시간에 일어나기", "오늘과 내일 같은 시간에 일어나 보세요.", "LIGHT"),
    ("SMOKE_DRINK", "오늘은 술 없는 날", "오늘 하루는 술 없이 보내 보세요.", "LIGHT"),
    ("SMOKE_DRINK", "첫 담배 30분 미루기", "피우고 싶을 때 물 한 잔 마시고 30분만 미뤄 보세요.", "LIGHT"),
    ("SMOKE_DRINK", "술자리에서 물 한 잔씩", "술 한 잔마다 물 한 잔을 함께 마셔 보세요.", "LIGHT"),
]


def seed_challenges(db: Session) -> None:
    if db.scalar(select(Challenge.id).limit(1)) is None:
        db.add_all(Challenge(category=c, title=t, description=d, intensity=i) for c, t, d, i in SEED_CHALLENGES)
        db.commit()


def recommended_categories(db: Session, user: User) -> list[dict]:
    """문진 답으로 개선이 필요한 카테고리를 우선순위대로 (REQ-009, 규칙 기반)."""
    q = pred.latest_questionnaire(db, user.user_id)
    if q is None:
        return [{"category": "DIET", "label": CATEGORY_LABELS["DIET"], "reason": "문진을 마치면 맞춤 추천을 드려요"}]
    out = []
    if (q.activity_days_per_week or 0) < 3:
        out.append(("ACTIVITY", "주 3일 미만으로 움직이고 있어요"))
    if (q.sleep_hours is not None and q.sleep_hours < 6.5) or q.sleep_trouble:
        out.append(("SLEEP_REST", "수면 시간이 짧거나 잠이 불편해요"))
    if q.smoking_status == "CURRENT" or (q.drinking_days_per_week or 0) >= 3:
        out.append(("SMOKE_DRINK", "흡연 또는 잦은 음주가 있어요"))
    out.append(("DIET", "식습관은 누구에게나 도움이 돼요"))
    return [{"category": c, "label": CATEGORY_LABELS[c], "reason": r} for c, r in out]


def today_missions(db: Session, user: User, date: dt.date | None = None) -> dict:
    """오늘의 미션. 없으면 추천 카테고리 순서로 하루 최대 3개 배정."""
    date = date or now().date()
    seed_challenges(db)
    stmt = select(DailyChallenge, Challenge).join(Challenge, Challenge.id == DailyChallenge.challenge_id).where(
        DailyChallenge.user_id == user.user_id, DailyChallenge.assigned_date == date).order_by(DailyChallenge.id)
    rows = db.execute(stmt).all()
    cats = recommended_categories(db, user)
    if not rows:
        q = pred.latest_questionnaire(db, user.user_id)
        restricted = bool(q and q.exercise_restricted)
        picked = []
        for i in range(3):
            cat = cats[i % len(cats)]["category"]
            pool = [c for c in db.scalars(select(Challenge).where(Challenge.category == cat, Challenge.is_active.is_(True))
                                          .order_by(Challenge.id))
                    if not (restricted and c.intensity == "HARD") and c.id not in picked]
            if pool:
                picked.append(pool[(date.toordinal() + i) % len(pool)].id)
        db.add_all(DailyChallenge(user_id=user.user_id, challenge_id=cid, assigned_date=date) for cid in picked)
        try:
            db.commit()
        except IntegrityError:  # 같은 순간에 다른 요청이 먼저 배정함 → 그 결과를 사용
            db.rollback()
        rows = db.execute(stmt).all()
    missions = [{"daily_challenge_id": d.id, "challenge_id": c.id, "category": c.category,
                 "category_label": CATEGORY_LABELS[c.category], "title": c.title, "description": c.description,
                 "intensity": c.intensity, "completed": d.is_completed} for d, c in rows]
    done = sum(m["completed"] for m in missions)
    return {"date": date.isoformat(), "missions": missions, "recommended_categories": cats,
            "completion_rate": round(done / len(missions), 2) if missions else 0.0, "streak_days": streak(db, user.user_id, date)}


def streak(db: Session, user_id: int, today: dt.date) -> int:
    days = set(db.scalars(select(DailyChallenge.assigned_date).where(DailyChallenge.user_id == user_id,
                                                                    DailyChallenge.is_completed.is_(True))))
    d, n = today if today in days else today - dt.timedelta(days=1), 0
    while d in days:
        n, d = n + 1, d - dt.timedelta(days=1)
    return n


def save_checkin(db: Session, user: User, body) -> tuple[dict, bool]:
    """체크인 저장. 같은 날 다시 보내면 덮어써요 (04 대조 5 임시 결정). 예측 재계산은 하지 않습니다."""
    date = body.checkin_date or now().date()
    today_missions(db, user, date)
    assigned = {d.id: d for d in db.scalars(select(DailyChallenge).where(DailyChallenge.user_id == user.user_id,
                                                                         DailyChallenge.assigned_date == date))}
    not_mine = [i for i in body.completed_daily_challenge_ids if i not in assigned]
    if not_mine:
        raise api_error(400, "VALIDATION_ERROR", f"이 날짜에 배정된 미션이 아니에요: {not_mine}")
    for d in assigned.values():
        done = d.id in body.completed_daily_challenge_ids
        if done and not d.is_completed:
            d.completed_at = now()
        d.is_completed = done
    checkin = db.scalar(select(Checkin).where(Checkin.user_id == user.user_id, Checkin.checkin_date == date))
    created = checkin is None
    if created:
        checkin = Checkin(user_id=user.user_id, checkin_date=date)
        db.add(checkin)
    for f in ("sleep_hours", "mood", "refreshed", "stress", "memo", "medication_taken"):
        if getattr(body, f) is not None:
            setattr(checkin, f, getattr(body, f))
    db.commit()
    done = sum(d.is_completed for d in assigned.values())
    from app.services import safety_service  # 메모는 서버 키워드 검사만 하고 LLM에 보내지 않음 (REQ-022 ④, REQ-034)
    crisis = safety_service.CRISIS if safety_service.matches(db, checkin.memo, "RISK_SIGNAL") else None
    return {"checkin_id": checkin.id, "checkin_date": date.isoformat(), "safety_alert": crisis,
            "completion_rate": round(done / len(assigned), 2) if assigned else 0.0,
            "streak_days": streak(db, user.user_id, date), "created_at": checkin.created_at.isoformat()}, created


def coach_today(db: Session, user: User) -> dict:
    """오늘의 코치 메시지: 하루 1회 만들고 저장본을 다시 써요 (NFR-007·010).

    LLM_API_KEY가 없으면 고정 문구로 만듭니다. 숫자는 서버가 넣고, LLM은 말투만 맡게 될 자리예요.
    """
    date = now().date()
    msg = db.scalar(select(CoachMessage).where(CoachMessage.user_id == user.user_id, CoachMessage.message_date == date))
    if msg is None:
        missions = today_missions(db, user, date)
        first = missions["missions"][0]["title"] if missions["missions"] else "가벼운 스트레칭"
        streak_days = missions["streak_days"]
        opener = f"{streak_days}일째 이어 가고 계세요. " if streak_days else "오늘도 찾아 주셔서 반가워요. "
        content = f"{user.name}님, {opener}오늘은 '{first}'부터 가볍게 시작해 볼까요? 못 한 날이 있어도 괜찮아요. 다시 시작하면 됩니다."
        from app.services import safety_service
        if safety_service.matches(db, content.replace(user.name, ""), "MEDICAL_BAN"):  # 금지어가 섞이면 안전한 기본 문구로 (NFR-014)
            content = "오늘도 찾아 주셔서 반가워요. 가벼운 실천 하나부터 시작해 볼까요?"
        source = "TEMPLATE"  # TODO(LLM 담당): LLM_API_KEY가 있으면 같은 사실 데이터로 문장만 다듬고, 금지어·수치 검사 후 저장
        _ = os.environ.get("LLM_API_KEY")
        msg = CoachMessage(user_id=user.user_id, message_date=date, content=content, source=source)
        db.add(msg)
        try:
            db.commit()
        except IntegrityError:  # 동시에 만들어졌으면 먼저 저장된 메시지를 사용
            db.rollback()
            msg = db.scalar(select(CoachMessage).where(CoachMessage.user_id == user.user_id, CoachMessage.message_date == date))
    return {"message_date": date.isoformat(), "content": msg.content, "source": msg.source,
            "disclaimer": "생활습관 관리 도움말이며 의학적 진단·처방이 아니에요."}
