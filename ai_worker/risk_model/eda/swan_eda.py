"""SWAN 기반 고LDL 발생 위험 예측 — 탐색적 분석 (AI 모델링 설계 v0.2 재현용)

사용법:
    1. ICPSR(시리즈 253)에서 기저·V1·V3~V7 자료를 SPSS 형식으로 내려받아 아래처럼 배치
       data/raw/swan/ICPSR_28762/DS0001/28762-0001-Data.sav   (기저)
       data/raw/swan/ICPSR_29221/...  29701  30142  30501  31181  31901
    2. uv run python ai_worker/risk_model/eda/swan_eda.py

주의: 원자료는 레포에 올리지 않는다 (.gitignore 로 data/ 전체 차단).
"""

from __future__ import annotations

import glob
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

DATA_DIR = Path("data/raw/swan")
VISITS = {
    0: "ICPSR_28762",
    1: "ICPSR_29221",
    3: "ICPSR_29701",
    4: "ICPSR_30142",
    5: "ICPSR_30501",
    6: "ICPSR_31181",
    7: "ICPSR_31901",
}

# 분석 변수
A_FEATURES = [
    "AGE0",
    "BMI0",
    "WAIST0",
    "peri",
    "HOTFLAS0",
    "NITESWE0",
    "smoke_now",
    "SPORTS0",
    "INCOME0",
    "sfat_pct",
    "sbp",
]
A_SERVICE = [c for c in A_FEATURES if c != "INCOME0"]  # 소득은 서비스에서 수집하지 않음
B_FEATURES = [*A_FEATURES, "LDLRESU0"]
B_PLUS = [*B_FEATURES, "HDLRESU0", "TRIGRES0", "CHOLRES0", "GLUCRES0"]


def sav_path(visit: int) -> str:
    """회차 번호로 .sav 파일 경로를 찾는다."""
    hits = glob.glob(str(DATA_DIR / VISITS[visit] / "DS0001" / "*-Data.sav"))
    if not hits:
        raise FileNotFoundError(f"V{visit} 자료가 없습니다: {DATA_DIR / VISITS[visit]}")
    return hits[0]


def clean(series: pd.Series) -> pd.Series:
    """SWAN 결측 코드(-9 Missing, -8 모름, -7 거부, -1 해당없음)를 결측으로 바꾼다."""
    s = pd.to_numeric(series, errors="coerce")
    return s.where(s > -1)


def load_baseline() -> pd.DataFrame:
    """기저 조사에서 분석 변수를 뽑아 파생 변수까지 만든다."""
    raw, _ = pyreadstat.read_sav(sav_path(0))
    cols = [
        "RACE",
        "AGE0",
        "STATUS0",
        "BMI0",
        "WAIST0",
        "HOTFLAS0",
        "NITESWE0",
        "SMOKERE0",
        "SMOKENO0",
        "SPORTS0",
        "INCOME0",
        "DTTKCAL0",
        "DTTSFAT0",
        "DTTFAT0",
        "SYSBP10",
        "SYSBP20",
        "LDLRESU0",
        "CHOLRES0",
        "HDLRESU0",
        "TRIGRES0",
        "GLUCRES0",
        "CHOLEST0",
        "HORMPIL0",
        "ESTRPTC0",
        "HORMCRE0",
    ]
    # .to_numpy()로 넣는다 — Series 그대로 넣으면 SWANID 인덱스에 재정렬되어 전부 결측이 된다
    b = pd.DataFrame({c: clean(raw[c]).to_numpy() for c in cols if c in raw}, index=pd.Index(raw.SWANID, name="SWANID"))
    b["sbp"] = b[["SYSBP10", "SYSBP20"]].mean(axis=1)

    # 복약·호르몬제: 코드 2 = Yes. 결측은 False로 뭉개지 않고 결측으로 남긴다.
    # 제외 기준에서 "미복용(False)"과 "정보 없음(결측)"을 구분하기 위함이다.
    b["med0"] = (b.CHOLEST0 == 2).where(b.CHOLEST0.notna())
    hrt_cols = ["HORMPIL0", "ESTRPTC0", "HORMCRE0"]
    b["hrt0"] = (b[hrt_cols] == 2).any(axis=1).where(b[hrt_cols].notna().any(axis=1))

    # 흡연: SMOKENO0(현재 흡연)은 SMOKERE0(흡연 경험)==2인 사람에게만 묻는다.
    # SMOKERE0==1(경험 없음)인 1,876명은 SMOKENO0이 전원 결측이며 이는 구조적 skip이므로
    # 비흡연(0)으로 확정한다. SMOKERE0 자체가 결측인 사람만 결측으로 남겨 대치에 맡긴다.
    b["smoke_now"] = np.where(
        b.SMOKERE0 == 1, 0.0, np.where(b.SMOKENO0 == 2, 1.0, np.where(b.SMOKENO0 == 1, 0.0, np.nan))
    )

    b["sfat_pct"] = 9 * b.DTTSFAT0 / b.DTTKCAL0 * 100  # 포화지방 열량 비율(%)
    b["peri"] = (b.STATUS0 == 4).astype(float)  # 4 = Early Peri
    return b


def missing_report(b: pd.DataFrame, cohort: pd.DataFrame) -> None:
    """분석 변수의 결측률을 출력한다 (문서 4.3 재현용)."""
    print("\n=== 분석 변수 결측률 ===")
    print(f"  {'변수':<12}{'기저 3,302명':>14}{'분석 대상':>12}")
    for col in [*B_PLUS, "RACE"]:
        if col not in b:
            continue
        print(f"  {col:<12}{100 * b[col].isna().mean():13.1f}%{100 * cohort[col].isna().mean():11.1f}%")


def load_followup() -> pd.DataFrame:
    """추적 회차의 LDL과 지질강하제 복용 여부를 긴 형식으로 모은다."""
    frames = []
    for v in VISITS:
        if v == 0:
            continue
        raw, _ = pyreadstat.read_sav(sav_path(v))
        ldl = clean(raw[f"LDLRESU{v}"]) if f"LDLRESU{v}" in raw else pd.Series(np.nan, index=raw.index)
        med = pd.to_numeric(raw.get(f"CHOLST1{v}"), errors="coerce") == 2
        frames.append(pd.DataFrame({"SWANID": raw.SWANID, "visit": v, "ldl": ldl.values, "med": med.values}))
    return pd.concat(frames, ignore_index=True)


def judgeable(fu: pd.DataFrame) -> pd.Series:
    """발생 여부를 판정할 수 있는 방문인지. LDL 측정됨 또는 지질강하제 복용 확인됨."""
    return fu.ldl.notna() | fu.med


def build_cohort(b: pd.DataFrame, fu: pd.DataFrame) -> pd.DataFrame:
    """제외 기준을 차례로 적용하고 각 단계 인원을 출력한다."""
    # 판정 가능 방문 = LDL이 측정됐거나 지질강하제 복용이 확인된 방문.
    # LDL 미측정 + 미복용 방문은 "LDL>=160 발생"을 배제할 수 없으므로 관찰로 치지 않는다.
    last_obs = fu[judgeable(fu)].groupby("SWANID").visit.max()
    steps = [("기저 조사 전체", b)]
    s = b[b.LDLRESU0.notna()]
    steps.append(("기저 LDL 측정됨", s))
    s = s[s.STATUS0.isin([3, 4, 5])]
    steps.append(("폐경 전 또는 이행기", s))
    s = s[s.med0 == False]  # noqa: E712 — 결측(정보 없음)은 제외한다
    steps.append(("기저 지질강하제 미복용 확인", s))
    s = s[s.hrt0 == False]  # noqa: E712
    steps.append(("기저 호르몬제 미사용 확인", s))
    s = s[s.LDLRESU0 < 160]
    steps.append(("기저 LDL < 160 (위험 집단)", s))
    s = s[s.index.isin(last_obs.index)]
    steps.append(("추적 관찰 1회 이상", s))

    print("=== 제외 기준별 대상자 수 ===")
    prev = None
    for name, frame in steps:
        drop = "" if prev is None else f"(-{prev - len(frame)})"
        print(f"  {name:30s} {len(frame):5d} {drop}")
        prev = len(frame)

    cohort = s.copy()
    cohort["last_obs"] = last_obs.reindex(cohort.index)
    return cohort


def label(fu: pd.DataFrame, cohort: pd.DataFrame, window: int, include_med: bool) -> pd.DataFrame:
    """기간 안의 발생 여부를 라벨로 만들고 판정 근거가 없는 사람을 제외한다."""
    f = fu[fu.visit.between(1, window)]
    if include_med:
        event = f.groupby("SWANID").apply(lambda g: bool((g.ldl >= 160).any() or g.med.any()))
    else:
        event = f.groupby("SWANID").apply(lambda g: bool((g.ldl >= 160).any()))
    d = cohort.copy()
    d["y"] = event.reindex(d.index).fillna(False).astype(bool)

    # 기간 안에 판정 가능 방문이 한 번도 없는 사람은 음성 라벨의 근거가 없으므로 제외한다.
    # 이 조건이 없으면 기간 밖(V6~V7)에만 관찰된 사람이 자동으로 음성이 된다.
    in_window = fu[fu.visit.between(1, window) & judgeable(fu)].SWANID.unique()
    keep = d.y | (d.last_obs >= window)
    return d[keep & d.index.isin(in_window)]


def cv_proba(d: pd.DataFrame, features: list[str], kind: str = "LR") -> np.ndarray:
    """5겹 교차검증 예측확률을 돌려준다. 대치·표준화는 폴드 안에서만 수행한다."""
    if kind == "LR":
        model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=3000))
    else:
        model = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.06, max_iter=250, random_state=0)
    return cross_val_predict(
        model,
        d[features].to_numpy(float),
        d.y.astype(int),
        cv=StratifiedKFold(5, shuffle=True, random_state=0),
        method="predict_proba",
    )[:, 1]


def cv_auroc(d: pd.DataFrame, features: list[str]) -> tuple[float, np.ndarray]:
    """AUROC와 예측확률을 함께 돌려준다."""
    proba = cv_proba(d, features)
    return roc_auc_score(d.y.astype(int), proba), proba


B_SERVICE = [*A_SERVICE, "LDLRESU0"]  # 서비스안: 소득 제외
VARIABLE_SETS = [
    ("A 문진·계측", A_FEATURES),
    ("A- 소득 제외", A_SERVICE),
    ("A- 포화지방도 제외", [c for c in A_SERVICE if c != "sfat_pct"]),
    ("B  A+LDL", B_FEATURES),
    ("B- 소득 제외", B_SERVICE),
    ("B- 포화지방도 제외", [c for c in B_SERVICE if c != "sfat_pct"]),
    ("B+ 지질 5종", B_PLUS),
    ("LDL 단독", ["LDLRESU0"]),
]


def compare_models(d: pd.DataFrame) -> None:
    """변수 세트 x 모델별로 지표 3개를 비교한다 (요구사항 DR-010)."""
    print("\n=== 변수 세트 x 모델 (AUROC / AUPRC / 상위 20% 선별 민감도) ===")
    y = d.y.astype(int).to_numpy()
    print(f"{'변수 세트':22s}{'모델':6s}{'AUROC':>8s}{'AUPRC':>8s}{'민감도':>8s}")
    for name, features in VARIABLE_SETS:
        for kind in ("LR", "GB"):
            p = cv_proba(d, features, kind)
            sens = recall_score(y, p >= np.quantile(p, 0.8))
            print(f"{name:22s}{kind:6s}{roc_auc_score(y, p):>8.3f}{average_precision_score(y, p):>8.3f}{sens:>8.3f}")


def calibration_report(d: pd.DataFrame) -> None:
    """보정 성능을 모델별로 비교한다 (DR-010 확률 보정 평가).

    Brier score는 낮을수록 좋다. 절편 0 / 기울기 1 이 완벽한 보정이고,
    기울기 < 1 은 과대 산포(극단 확률을 너무 자신 있게 내놓음)를 뜻한다.
    ECE는 10분위 안에서 |예측 평균 − 실제 발생률|을 인원 가중 평균한 값이다.
    """
    print("\n=== 보정 성능 비교 (DR-010) ===")
    y = d.y.astype(int).to_numpy()
    base = y.mean()
    print(
        f"  무정보 기준선(항상 {100 * base:.1f}% 예측) Brier = {brier_score_loss(y, np.full_like(y, base, dtype=float)):.4f}"
    )
    print(f"  {'모델':<22}{'Brier':>9}{'절편':>8}{'기울기':>8}{'ECE':>8}{'최대편차':>9}")
    for name, features in [("B  A+LDL", B_FEATURES), ("B- 서비스안", B_SERVICE), ("LDL 단독", ["LDLRESU0"])]:
        p = np.clip(cv_proba(d, features), 1e-6, 1 - 1e-6)
        logit = np.log(p / (1 - p)).reshape(-1, 1)
        recal = LogisticRegression().fit(logit, y)
        slope = float(recal.coef_[0][0])
        intercept = float(recal.intercept_[0])
        q = pd.qcut(p, 10, labels=False, duplicates="drop")
        gaps, sizes = [], []
        for g in np.unique(q):
            m = q == g
            gaps.append(abs(p[m].mean() - y[m].mean()))
            sizes.append(m.sum())
        ece = float(np.average(gaps, weights=sizes))
        print(
            f"  {name:<22}{brier_score_loss(y, p):>9.4f}{intercept:>8.3f}{slope:>8.3f}"
            f"{100 * ece:>7.1f}%{100 * max(gaps):>8.1f}%"
        )


def calibration_curve_table(d: pd.DataFrame, features: list[str], label_name: str, bins: int = 10) -> None:
    """10분위 보정 곡선 수치를 표로 낸다."""
    y = d.y.astype(int).to_numpy()
    p = cv_proba(d, features)
    q = pd.qcut(p, bins, labels=False, duplicates="drop")
    print(f"\n=== 보정 곡선 10분위 — {label_name} ===")
    print(f"  {'분위':>4}{'n':>7}{'예측 평균':>11}{'실제 발생률':>13}{'차이':>9}")
    for g in np.unique(q):
        m = q == g
        pred, obs = 100 * p[m].mean(), 100 * y[m].mean()
        print(f"  {g + 1:>4}{int(m.sum()):>7}{pred:>10.1f}%{obs:>12.1f}%{obs - pred:>+8.1f}%p")


def coefficients(d: pd.DataFrame) -> None:
    """서비스안(B-) 로지스틱 회귀의 표준화 계수를 낸다 (문서 5.5 재현용)."""
    print("\n=== B- 서비스안 표준화 회귀계수 (전체 적합) ===")
    pipe = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=3000))
    pipe.fit(d[B_SERVICE].to_numpy(float), d.y.astype(int))
    coef = pipe[-1].coef_[0]
    order = np.argsort(-np.abs(coef))
    print("  ※ 표준화 계수이므로 변수 간 크기 비교는 가능하나 인과적 해석은 불가 (SR-027)")
    for i in order:
        print(f"  {B_SERVICE[i]:<12}{coef[i]:>+8.3f}")


def performance_by_ldl(d: pd.DataFrame, proba: np.ndarray) -> None:
    """기저 LDL 구간 안에서도 변별력이 있는지 확인한다 (기획안 v2 13.3)."""
    print("\n=== 기저 LDL 구간별 모델 성능 ===")
    y = d.y.astype(int).to_numpy()
    for low, high in ((0, 100), (100, 130), (130, 145), (145, 160)):
        mask = ((d.LDLRESU0 >= low) & (d.LDLRESU0 < high)).to_numpy()
        n, k = int(mask.sum()), int(y[mask].sum())
        auroc = roc_auc_score(y[mask], proba[mask]) if 0 < k < n else float("nan")
        print(
            f"  LDL {low:3d}~{high:3d}  n={n:4d}  발생={k:3d} ({100 * k / n:4.1f}%)  "
            f"구간 내 AUROC={auroc:.3f}  예측확률 평균={100 * proba[mask].mean():4.1f}%"
        )


def performance_by_race(d: pd.DataFrame, proba: np.ndarray, n_boot: int = 2000) -> None:
    """인종별 하위 성능을 신뢰구간과 함께 낸다 (문서 7.1 — 참고용, 표본이 작다)."""
    names = {1: "흑인", 2: "중국계", 3: "일본계", 4: "백인", 5: "히스패닉"}
    y = d.y.astype(int).to_numpy()
    race = d.RACE.to_numpy()
    rng = np.random.default_rng(0)
    print("\n=== 인종별 하위 성능 (참고용) ===")
    print(f"  {'집단':<9}{'n':>6}{'발생':>6}{'AUROC':>8}{'  95% CI':>20}{'  CI 폭':>9}")
    for code, name in names.items():
        mask = race == code
        yy, pp = y[mask], proba[mask]
        if yy.sum() < 5:
            continue
        boots = []
        for _ in range(n_boot):
            idx = rng.integers(0, len(yy), len(yy))
            if len(np.unique(yy[idx])) > 1:
                boots.append(roc_auc_score(yy[idx], pp[idx]))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        print(
            f"  {name:<9}{len(yy):>6}{int(yy.sum()):>6}{roc_auc_score(yy, pp):>8.3f}"
            f"   [{lo:.3f}, {hi:.3f}]{hi - lo:>9.3f}"
        )
    print("  ※ 신뢰구간이 서로 겹치므로 집단 간 순위는 주장할 수 없다. 개별 수치 단독 인용 금지.")


def censoring_check(cohort: pd.DataFrame, analyzed: pd.DataFrame) -> None:
    """중도절단된 사람과 분석 대상의 특성을 비교한다 (선택편향 점검)."""
    print("\n=== 중도절단 선택편향 점검 ===")
    censored = cohort[~cohort.index.isin(analyzed.index)]
    for col, name in (
        ("AGE0", "나이"),
        ("BMI0", "BMI"),
        ("WAIST0", "허리둘레"),
        ("LDLRESU0", "기저 LDL"),
        ("smoke_now", "현재 흡연율"),
    ):
        print(f"  {name:9s} 분석 {analyzed[col].mean():6.2f}   중도절단 {censored[col].mean():6.2f}")


def compare_windows(cohort: pd.DataFrame, fu: pd.DataFrame) -> None:
    """예측 기간 × 발생 정의 조합을 비교한다."""
    print("\n=== 예측 기간 × 발생 정의 ===")
    print(
        f"{'기간':8s}{'정의':20s}{'분석':>6s}{'중도절단':>8s}{'발생':>6s}{'발생률':>8s}"
        f"{'A':>8s}{'B':>8s}{'B+':>8s}{'LDL단독':>9s}"
    )
    for window in (3, 5, 7):
        for include_med, name in ((False, "LDL>=160 단독"), (True, "+약 시작")):
            d = label(fu, cohort, window, include_med)
            censored = len(cohort) - len(d)
            scores = [cv_auroc(d, fs)[0] for fs in (A_FEATURES, B_FEATURES, B_PLUS, ["LDLRESU0"])]
            print(
                f"{window}년{'':4s}{name:20s}{len(d):>6d}{censored:>8d}{int(d.y.sum()):>6d}"
                f"{100 * d.y.mean():>7.1f}%" + "".join(f"{s:>8.3f}" for s in scores[:3]) + f"{scores[3]:>9.3f}"
            )


def bootstrap_gap(d: pd.DataFrame, n_boot: int = 2000) -> None:
    """B 모델과 LDL 단독의 AUROC 차이를 부트스트랩으로 비교한다."""
    y = d.y.astype(int).to_numpy()
    _, p_b = cv_auroc(d, B_FEATURES)
    _, p_ldl = cv_auroc(d, ["LDLRESU0"])
    rng = np.random.default_rng(0)
    diffs = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        if 0 < y[idx].sum() < len(idx):
            diffs.append(roc_auc_score(y[idx], p_b[idx]) - roc_auc_score(y[idx], p_ldl[idx]))
    diffs = np.array(diffs)
    print(f"\n=== B(A+LDL) vs LDL 단독 (부트스트랩 {n_boot}회) ===")
    print(
        f"  B={roc_auc_score(y, p_b):.3f}  LDL단독={roc_auc_score(y, p_ldl):.3f}  "
        f"차이={diffs.mean():+.4f}  95% CI [{np.percentile(diffs, 2.5):+.4f}, "
        f"{np.percentile(diffs, 97.5):+.4f}]"
    )
    return p_b


def report_risk_groups(d: pd.DataFrame, proba: np.ndarray) -> None:
    """기저 LDL 구간별 발생률과 예측확률 보정 상태를 출력한다."""
    print("\n=== 기저 LDL 구간별 발생률 ===")
    g = d.groupby(pd.cut(d.LDLRESU0, [0, 100, 130, 145, 160], right=False)).y.agg(["size", "sum", "mean"])
    g.columns = ["인원", "발생", "발생률"]
    g["발생률"] = (100 * g["발생률"]).round(1)
    print(g.to_string())

    print("\n=== 예측확률 5분위별 실제 발생률 (보정 확인) ===")
    t = pd.DataFrame(
        {
            "q": pd.qcut(proba, 5, labels=["최저", "낮음", "중간", "높음", "최고"]),
            "y": d.y.astype(int).to_numpy(),
            "p": proba,
        }
    )
    out = t.groupby("q").agg(인원=("y", "size"), 예측평균=("p", "mean"), 실제발생률=("y", "mean"))
    print(
        (
            out.assign(
                예측평균=lambda x: (100 * x.예측평균).round(1), 실제발생률=lambda x: (100 * x.실제발생률).round(1)
            )
        ).to_string()
    )


def main() -> None:
    baseline = load_baseline()
    followup = load_followup()
    cohort = build_cohort(baseline, followup)
    compare_windows(cohort, followup)

    primary = label(followup, cohort, window=5, include_med=True)  # 권고안
    print(
        f"\n[권고안: 5년 내 LDL>=160 또는 약 시작] n={len(primary)} "
        f"발생={int(primary.y.sum())} ({100 * primary.y.mean():.1f}%)"
    )
    missing_report(baseline, primary)
    compare_models(primary)
    proba = bootstrap_gap(primary)
    report_risk_groups(primary, proba)
    performance_by_ldl(primary, proba)
    performance_by_race(primary, proba)
    censoring_check(cohort, primary)
    calibration_report(primary)
    calibration_curve_table(primary, B_SERVICE, "B- 서비스안")
    calibration_curve_table(primary, ["LDLRESU0"], "LDL 단독")
    coefficients(primary)


if __name__ == "__main__":
    main()
