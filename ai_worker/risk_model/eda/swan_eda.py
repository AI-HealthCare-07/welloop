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
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

DATA_DIR = Path("data/raw/swan")
VISITS = {0: "ICPSR_28762", 1: "ICPSR_29221", 3: "ICPSR_29701",
          4: "ICPSR_30142", 5: "ICPSR_30501", 6: "ICPSR_31181", 7: "ICPSR_31901"}

# 분석 변수
A_FEATURES = ["AGE0", "BMI0", "WAIST0", "peri", "HOTFLAS0", "NITESWE0",
              "smoke_now", "SPORTS0", "INCOME0", "sfat_pct", "sbp"]
A_SERVICE = [c for c in A_FEATURES if c != "INCOME0"]   # 소득은 서비스에서 수집하지 않음
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
    cols = ["RACE", "AGE0", "STATUS0", "BMI0", "WAIST0", "HOTFLAS0", "NITESWE0",
            "SMOKERE0", "SMOKENO0", "SPORTS0", "INCOME0",
            "DTTKCAL0", "DTTSFAT0", "DTTFAT0", "SYSBP10", "SYSBP20",
            "LDLRESU0", "CHOLRES0", "HDLRESU0", "TRIGRES0", "GLUCRES0",
            "CHOLEST0", "HORMPIL0", "ESTRPTC0", "HORMCRE0"]
    # .to_numpy()로 넣는다 — Series 그대로 넣으면 SWANID 인덱스에 재정렬되어 전부 결측이 된다
    b = pd.DataFrame({c: clean(raw[c]).to_numpy() for c in cols if c in raw},
                     index=pd.Index(raw.SWANID, name="SWANID"))
    b["sbp"] = b[["SYSBP10", "SYSBP20"]].mean(axis=1)
    b["med0"] = b.CHOLEST0 == 2                                   # 2 = Yes
    b["hrt0"] = (b.HORMPIL0 == 2) | (b.ESTRPTC0 == 2) | (b.HORMCRE0 == 2)
    b["smoke_now"] = (b.SMOKENO0 == 2).astype(float)
    b["sfat_pct"] = 9 * b.DTTSFAT0 / b.DTTKCAL0 * 100             # 포화지방 열량 비율(%)
    b["peri"] = (b.STATUS0 == 4).astype(float)                    # 4 = Early Peri
    return b


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


def build_cohort(b: pd.DataFrame, fu: pd.DataFrame) -> pd.DataFrame:
    """제외 기준을 차례로 적용하고 각 단계 인원을 출력한다."""
    last_obs = fu[fu.ldl.notna() | fu.med].groupby("SWANID").visit.max()
    steps = [("기저 조사 전체", b)]
    s = b[b.LDLRESU0.notna()];              steps.append(("기저 LDL 측정됨", s))
    s = s[s.STATUS0.isin([3, 4, 5])];       steps.append(("폐경 전 또는 이행기", s))
    s = s[~s.med0];                         steps.append(("기저 지질강하제 미복용", s))
    s = s[~s.hrt0];                         steps.append(("기저 호르몬제 미사용", s))
    s = s[s.LDLRESU0 < 160];                steps.append(("기저 LDL < 160 (위험 집단)", s))
    s = s[s.index.isin(last_obs.index)];    steps.append(("추적 관찰 1회 이상", s))

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
    """기간 안의 발생 여부를 라벨로 만들고 중도절단된 사람을 제외한다."""
    f = fu[fu.visit.between(1, window)]
    if include_med:
        event = f.groupby("SWANID").apply(lambda g: bool((g.ldl >= 160).any() or g.med.any()))
    else:
        event = f.groupby("SWANID").apply(lambda g: bool((g.ldl >= 160).any()))
    d = cohort.copy()
    d["y"] = event.reindex(d.index).fillna(False)
    return d[d.y | (d.last_obs >= window)]          # 발생했거나 기간 끝까지 관찰된 사람만


def cv_proba(d: pd.DataFrame, features: list[str], kind: str = "LR") -> np.ndarray:
    """5겹 교차검증 예측확률을 돌려준다. 대치·표준화는 폴드 안에서만 수행한다."""
    if kind == "LR":
        model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                              LogisticRegression(max_iter=3000))
    else:
        model = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.06,
                                               max_iter=250, random_state=0)
    return cross_val_predict(model, d[features].to_numpy(float), d.y.astype(int),
                             cv=StratifiedKFold(5, shuffle=True, random_state=0),
                             method="predict_proba")[:, 1]


def cv_auroc(d: pd.DataFrame, features: list[str]) -> tuple[float, np.ndarray]:
    """AUROC와 예측확률을 함께 돌려준다."""
    proba = cv_proba(d, features)
    return roc_auc_score(d.y.astype(int), proba), proba


def compare_models(d: pd.DataFrame) -> None:
    """변수 세트 x 모델별로 지표 3개를 비교한다 (요구사항 NFR-006)."""
    print("\n=== 변수 세트 x 모델 (AUROC / AUPRC / 상위 20% 선별 민감도) ===")
    y = d.y.astype(int).to_numpy()
    sets = [("A 문진·계측", A_FEATURES), ("A- 소득 제외", A_SERVICE),
            ("B  A+LDL", B_FEATURES), ("B- 소득 제외", [*A_SERVICE, "LDLRESU0"]),
            ("B+ 지질 5종", B_PLUS), ("LDL 단독", ["LDLRESU0"])]
    print(f"{'변수 세트':20s}{'모델':6s}{'AUROC':>8s}{'AUPRC':>8s}{'민감도':>8s}")
    for name, features in sets:
        for kind in ("LR", "GB"):
            p = cv_proba(d, features, kind)
            sens = recall_score(y, p >= np.quantile(p, 0.8))
            print(f"{name:20s}{kind:6s}{roc_auc_score(y, p):>8.3f}"
                  f"{average_precision_score(y, p):>8.3f}{sens:>8.3f}")


def performance_by_ldl(d: pd.DataFrame, proba: np.ndarray) -> None:
    """기저 LDL 구간 안에서도 변별력이 있는지 확인한다 (기획안 v2 13.3)."""
    print("\n=== 기저 LDL 구간별 모델 성능 ===")
    y = d.y.astype(int).to_numpy()
    for low, high in ((0, 100), (100, 130), (130, 145), (145, 160)):
        mask = ((d.LDLRESU0 >= low) & (d.LDLRESU0 < high)).to_numpy()
        n, k = int(mask.sum()), int(y[mask].sum())
        auroc = roc_auc_score(y[mask], proba[mask]) if 0 < k < n else float("nan")
        print(f"  LDL {low:3d}~{high:3d}  n={n:4d}  발생={k:3d} ({100 * k / n:4.1f}%)  "
              f"구간 내 AUROC={auroc:.3f}  예측확률 평균={100 * proba[mask].mean():4.1f}%")


def censoring_check(cohort: pd.DataFrame, analyzed: pd.DataFrame) -> None:
    """중도절단된 사람과 분석 대상의 특성을 비교한다 (선택편향 점검)."""
    print("\n=== 중도절단 선택편향 점검 ===")
    censored = cohort[~cohort.index.isin(analyzed.index)]
    for col, name in (("AGE0", "나이"), ("BMI0", "BMI"), ("WAIST0", "허리둘레"),
                      ("LDLRESU0", "기저 LDL"), ("smoke_now", "현재 흡연율")):
        print(f"  {name:9s} 분석 {analyzed[col].mean():6.2f}   중도절단 {censored[col].mean():6.2f}")


def compare_windows(cohort: pd.DataFrame, fu: pd.DataFrame) -> None:
    """예측 기간 × 발생 정의 조합을 비교한다."""
    print("\n=== 예측 기간 × 발생 정의 ===")
    print(f"{'기간':8s}{'정의':20s}{'분석':>6s}{'중도절단':>8s}{'발생':>6s}{'발생률':>8s}"
          f"{'A':>8s}{'B':>8s}{'B+':>8s}{'LDL단독':>9s}")
    for window in (3, 5, 7):
        for include_med, name in ((False, "LDL>=160 단독"), (True, "+약 시작")):
            d = label(fu, cohort, window, include_med)
            censored = len(cohort) - len(d)
            scores = [cv_auroc(d, fs)[0] for fs in (A_FEATURES, B_FEATURES, B_PLUS, ["LDLRESU0"])]
            print(f"{window}년{'':4s}{name:20s}{len(d):>6d}{censored:>8d}{int(d.y.sum()):>6d}"
                  f"{100 * d.y.mean():>7.1f}%" + "".join(f"{s:>8.3f}" for s in scores[:3])
                  + f"{scores[3]:>9.3f}")


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
    print(f"  B={roc_auc_score(y, p_b):.3f}  LDL단독={roc_auc_score(y, p_ldl):.3f}  "
          f"차이={diffs.mean():+.4f}  95% CI [{np.percentile(diffs, 2.5):+.4f}, "
          f"{np.percentile(diffs, 97.5):+.4f}]")
    return p_b


def report_risk_groups(d: pd.DataFrame, proba: np.ndarray) -> None:
    """기저 LDL 구간별 발생률과 예측확률 보정 상태를 출력한다."""
    print("\n=== 기저 LDL 구간별 발생률 ===")
    g = d.groupby(pd.cut(d.LDLRESU0, [0, 100, 130, 145, 160], right=False)).y.agg(["size", "sum", "mean"])
    g.columns = ["인원", "발생", "발생률"]
    g["발생률"] = (100 * g["발생률"]).round(1)
    print(g.to_string())

    print("\n=== 예측확률 5분위별 실제 발생률 (보정 확인) ===")
    t = pd.DataFrame({"q": pd.qcut(proba, 5, labels=["최저", "낮음", "중간", "높음", "최고"]),
                      "y": d.y.astype(int).to_numpy(), "p": proba})
    out = t.groupby("q").agg(인원=("y", "size"), 예측평균=("p", "mean"), 실제발생률=("y", "mean"))
    print((out.assign(예측평균=lambda x: (100 * x.예측평균).round(1),
                      실제발생률=lambda x: (100 * x.실제발생률).round(1))).to_string())


def main() -> None:
    baseline = load_baseline()
    followup = load_followup()
    cohort = build_cohort(baseline, followup)
    compare_windows(cohort, followup)

    primary = label(followup, cohort, window=5, include_med=True)   # 권고안
    print(f"\n[권고안: 5년 내 LDL>=160 또는 약 시작] n={len(primary)} "
          f"발생={int(primary.y.sum())} ({100 * primary.y.mean():.1f}%)")
    compare_models(primary)
    proba = bootstrap_gap(primary)
    report_risk_groups(primary, proba)
    performance_by_ldl(primary, proba)
    censoring_check(cohort, primary)


if __name__ == "__main__":
    main()
