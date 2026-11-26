"""모델 2(이행기 후기·폐경 후) 코호트 가능성 확인 — 11/25 회의 체크리스트 6번.

팀 결정(2026-11-25)에 따른 설계:
  1) 출발점 = 해당 단계에 **처음 들어선 방문** 1회만 (1인 1건, 중복 없음)
  2) 그 시점에 LDL < 160 · 지질강하제 미사용 · 호르몬제 미사용 · 자궁절제 없음
  3) 지질 검사가 V7까지라 5년 추적이 부족하면 3년도 비교
  4) 출발점 **이후** 정보는 입력 변수로 쓰지 않는다 (누수 방지)

이 스크립트는 **규모만 센다.** 학습도 평가도 하지 않는다.

필요한 자료 — ICPSR 시리즈 253의 **11개 자료 전부**. `swan_eda.py`는 지질 검사가 있는
7개만 쓰지만, 이 스크립트는 **모든 회차의 STATUS와 AGE**가 필요하다. 단계에 처음
들어선 방문을 찾고 창을 실제 경과 연수로 재기 때문이다.

    data/raw/swan/ICPSR_28762  (V0 기저)   29221 (V1)  29401 (V2)  29701 (V3)
                   30142 (V4)  30501 (V5)  31181 (V6)  31901 (V7)
                   32122 (V8)  32721 (V9)  32961 (V10)

V2·V8·V9·V10에는 지질 검사가 없다. 그래도 STATUS·AGE가 있어 단계 판정과 경과 연수
계산에 쓰인다.

실행:
    uv run python -m ai_worker.risk_model.model2_cohort
"""

from __future__ import annotations

import glob

import pandas as pd
import pyreadstat

BASE = "data/raw/swan"
MISSING = [-9, -8, -7, -1]

# STATUS 코드 — ICPSR 28762 코드북에서 확인
LATE_PERI = (3,)  # Late Peri
POST = (1, 2)  # 1 = Post by BSO, 2 = Natural Post

# 호르몬제 사용으로 간주할 변수 접두사. 코드 2 = Yes.
HRT_PREFIXES = ("ESTROG", "ESTRNJ", "PROGES", "HORMOTH", "HORMPIL", "ESTRPTC", "HORMCRE")

RACE_LABELS = {1: "흑인계", 2: "중국계", 3: "일본계", 4: "백인계", 5: "히스패닉"}

# 모델 1의 C3 8개 변수에 대응하는 회차별 변수 이름. 흡연만 회차마다 다르다.
SMOKE_CANDIDATES = ("SMOKER{v}", "SMOKENO{v}", "SMOKERE{v}")


def visit_file(v: int) -> str | None:
    """STATUS{v}를 담은 .sav 경로."""
    for p in sorted(glob.glob(f"{BASE}/ICPSR_*")):
        found = glob.glob(f"{p}/**/*.sav", recursive=True)
        if not found:
            continue
        _, m = pyreadstat.read_sav(found[0], metadataonly=True)
        if f"STATUS{v}" in m.column_names:
            return found[0]
    return None


def clean(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").mask(lambda x: x.isin(MISSING))


def read_visit(v: int) -> pd.DataFrame | None:
    """한 회차에서 출발점 판정에 필요한 변수만 읽는다."""
    path = visit_file(v)
    if path is None:
        return None
    _, m = pyreadstat.read_sav(path, metadataonly=True)
    want = [f"STATUS{v}", f"LDLRESU{v}", f"CHOLST1{v}", f"HYSTERE{v}", f"AGE{v}"]
    hrt = [c for c in m.column_names if c.upper().startswith(HRT_PREFIXES)]
    use = ["SWANID"] + [c for c in want + hrt if c in m.column_names]
    raw, _ = pyreadstat.read_sav(path, usecols=use)
    df = pd.DataFrame(index=pd.Index(raw.SWANID, name="SWANID"))
    for c in use[1:]:
        df[c] = clean(raw[c]).to_numpy()
    out = pd.DataFrame(index=df.index)
    out["visit"] = v
    out["age0"] = df.get(f"AGE{v}")
    out["status"] = df.get(f"STATUS{v}")
    out["ldl"] = df.get(f"LDLRESU{v}")
    out["med"] = df.get(f"CHOLST1{v}") == 2
    out["hyst"] = df[f"HYSTERE{v}"] == 2 if f"HYSTERE{v}" in df else False
    out["hrt"] = (df[hrt] == 2).any(axis=1) if hrt else False
    return out


def followup() -> pd.DataFrame:
    """판정 가능 방문을 긴 형식으로. **나이를 함께 싣는다.**

    창은 회차 번호가 아니라 실제 경과 연수로 재야 한다. 회차 번호로 세면
    지질 검사가 없는 회차(V2·V8~V10)를 1년으로 세게 되어 결과가 왜곡된다.
    """
    frames = []
    for v in range(1, 11):
        path = visit_file(v)
        if path is None:
            continue
        _, m = pyreadstat.read_sav(path, metadataonly=True)
        want = [c for c in (f"LDLRESU{v}", f"CHOLST1{v}", f"AGE{v}") if c in m.column_names]
        raw, _ = pyreadstat.read_sav(path, usecols=["SWANID"] + want)
        age = clean(raw[f"AGE{v}"]).to_numpy() if f"AGE{v}" in want else None
        ldl = clean(raw[f"LDLRESU{v}"]).to_numpy() if f"LDLRESU{v}" in want else None
        med = (clean(raw[f"CHOLST1{v}"]) == 2).to_numpy() if f"CHOLST1{v}" in want else False
        frames.append(pd.DataFrame({"SWANID": raw.SWANID, "age": age, "ldl": ldl, "med": med}))
    fu = pd.concat(frames, ignore_index=True)
    return fu[fu.age.notna() & (fu.ldl.notna() | fu.med)]


def index_cohort(visits: list[pd.DataFrame], stages: tuple[int, ...], name: str) -> pd.DataFrame:
    """각 여성이 해당 단계에 처음 들어선 방문을 출발점으로 잡고 제외 기준을 적용한다."""
    hit = pd.concat(visits).reset_index()
    hit = hit[hit.status.isin(stages)].sort_values(["SWANID", "visit"])
    first = hit.drop_duplicates("SWANID", keep="first")

    print(f"\n### {name} — 제외 기준별 인원")
    print(f"  {'처음 들어선 여성':<28} {len(first):>5}")
    steps = [
        ("그 시점 LDL 측정됨", lambda d: d[d.ldl.notna()]),
        ("지질강하제 미사용", lambda d: d[~d.med.astype(bool)]),
        ("호르몬제 미사용", lambda d: d[~d.hrt.astype(bool)]),
        ("자궁절제 없음", lambda d: d[~d.hyst.astype(bool)]),
        ("LDL < 160 (위험 집단)", lambda d: d[d.ldl < 160]),
        ("출발점 나이 확인됨", lambda d: d[d.age0.notna()]),
    ]
    s = first
    for label, fn in steps:
        prev = len(s)
        s = fn(s)
        print(f"  {label:<28} {len(s):>5}  ({len(s) - prev:+d})")
    return s.set_index("SWANID")


def outcome(cohort: pd.DataFrame, fu: pd.DataFrame, window: float, strict: bool) -> tuple[int, int]:
    """창 안의 발생 여부를 센다. 창은 실제 경과 연수로 잰다.

    strict=False: 음성만 창 끝까지 관찰을 요구한다 (모델 1과 같은 규칙).
    strict=True : 양성에게도 창 끝까지 관찰을 요구한다 (민감도 분석).

    지질 검사가 V7에서 끝나므로 출발점이 늦으면 음성 근거를 얻을 수 없어 제외된다.
    이 제외를 생략하면 양성만 남아 발생률이 터무니없이 높아진다.
    """
    by_id = {sid: g for sid, g in fu.groupby("SWANID")}
    kept = events = 0
    for sid, row in cohort.iterrows():
        g = by_id.get(sid)
        if g is None:
            continue
        g = g[g.age > row.age0 + 0.25]  # 같은 방문의 재측정은 제외
        if g.empty:
            continue
        inside = g[(g.age - row.age0) <= window]
        if inside.empty:
            continue  # 창 안에 판정 가능 방문이 없으면 음성 근거도 없다
        pos = bool((inside.ldl >= 160).any() or inside.med.any())
        full = (g.age.max() - row.age0) >= window
        if not full and (strict or not pos):
            continue
        kept += 1
        events += pos
    return kept, events


def report_windows(cohort: pd.DataFrame, fu: pd.DataFrame, name: str) -> None:
    """창 길이별 규모를 출력한다."""
    print(f"\n### {name} — 추적 창별 결과 (출발점 {len(cohort)}명)")
    print(f"  {'창':<6}{'추적 충족':>10}{'발생':>7}{'발생률':>9}{'사건/변수':>11}{'검증 30%':>10}")
    for w in (3.0, 4.0, 5.0):
        kept, ev = outcome(cohort, fu, w, strict=False)
        rate = f"{ev / kept * 100:.1f}%" if kept else "—"
        ratio = f"{ev / 8:.1f}" if kept else "—"
        print(f"  {int(w)}년 {kept:>10}{ev:>7}{rate:>9}{ratio:>11}{int(kept * 0.3):>10}")
    print("\n  민감도 분석 — 양성에게도 창 끝까지 관찰을 요구하면")
    for w in (3.0, 5.0):
        kept, ev = outcome(cohort, fu, w, strict=True)
        rate = f"{ev / kept * 100:.1f}%" if kept else "—"
        print(f"    {int(w)}년: 추적 완료 {kept}명, 발생 {ev}명 ({rate})")
    print(f"\n  출발점 회차 분포: {cohort.visit.value_counts().sort_index().to_dict()}")


def smoking_variables() -> None:
    """회차별 흡연 변수 가용성. 모델 1의 smoke_now를 그대로 재현할 수 있는지 본다."""
    print("\n### 회차별 흡연 변수 — 모델 1과 정의가 다르다")
    print(f"  {'회차':<6}{'SMOKER':>9}{'SMOKENO':>10}{'SMOKERE':>10}")
    for v in (0, 1, 3, 4, 5, 6, 7):
        path = visit_file(v)
        if path is None:
            continue
        _, m = pyreadstat.read_sav(path, metadataonly=True)
        marks = ["O" if c.format(v=v) in m.column_names else "×" for c in SMOKE_CANDIDATES]
        print(f"  V{v:<5}{marks[0]:>9}{marks[1]:>10}{marks[2]:>10}")
    print("  기저는 SMOKERE0(경험)+SMOKENO0(현재)의 2단 문항으로 '현재 흡연'을 만들었다.")
    print("  V3 이후에는 SMOKENO가 없어 SMOKERE('지난 방문 이후 규칙적 흡연')로 대체해야 한다.")


def race_mix() -> None:
    """모델 1 코호트의 인종·민족 구성. 집단별 제외 검증 계획의 근거."""
    from ai_worker.risk_model.eda.swan_eda import (
        build_cohort,
        label,
        load_baseline,
        load_followup,
    )

    path = visit_file(0)
    if path is None:
        return
    raw, _ = pyreadstat.read_sav(path, usecols=["SWANID", "RACE"])
    race = pd.Series(raw.RACE.to_numpy(), index=pd.Index(raw.SWANID, name="SWANID"))
    base = load_baseline()
    fu1 = load_followup()
    d = label(fu1, build_cohort(base, fu1), window=5, include_med=True)
    r = race.reindex(d.index)

    print("\n### 모델 1 분석 코호트의 인종·민족 구성 (집단별 제외 검증용)")
    print(f"  {'집단':<10}{'인원':>7}{'발생':>7}{'발생률':>9}")
    for code, name in RACE_LABELS.items():
        sel = r == code
        n = int(sel.sum())
        if n:
            print(f"  {name:<10}{n:>7}{int(d.y[sel].sum()):>7}{d.y[sel].mean() * 100:>8.1f}%")
    ea = r.isin([2, 3])
    print(f"\n  동아시아계(중국+일본) {int(ea.sum())}명, 발생 {int(d.y[ea].sum())}명 ({d.y[ea].mean() * 100:.1f}%)")
    print(f"  전체 {len(d)}명, 발생률 {d.y.mean() * 100:.1f}%")
    print("  공개 데이터(ICPSR 28762)에는 연구 기관 변수가 없어 기관별 제외 검증은 불가능하다.")


def model1_short_window() -> None:
    """모델 1을 3년 창으로 다시 라벨링하면 규모가 어떻게 되는지. 기간 통일 선택지 검토용."""
    from ai_worker.risk_model.eda.swan_eda import (
        build_cohort,
        label,
        load_baseline,
        load_followup,
    )

    base = load_baseline()
    fu1 = load_followup()
    coh = build_cohort(base, fu1)
    print("\n### 모델 1을 3년 창으로 바꾸면 (예측 기간 통일 선택지)")
    for w in (5, 3):
        d = label(fu1, coh, window=w, include_med=True)
        print(f"  {w}년 창: {len(d)}명, 발생 {int(d.y.sum())}명 ({d.y.mean() * 100:.1f}%)")


def main() -> None:
    visits = [df for v in range(1, 11) if (df := read_visit(v)) is not None]
    print(f"STATUS 변수가 있는 회차: V1~V{len(visits)}")
    fu = followup()

    for stages, name in ((LATE_PERI, "이행기 후기"), (POST, "폐경 후")):
        cohort = index_cohort(visits, stages, name)
        report_windows(cohort, fu, name)

    smoking_variables()
    model1_short_window()
    race_mix()


if __name__ == "__main__":
    main()
