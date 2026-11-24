"""SWAN 고LDL 발생 위험 — 홀드아웃 검증과 변수 구성 확정 (요구사항 DR-019).

왜 필요한가:
    설계 v0.2의 모든 수치는 교차검증값이고, 변수·모델 선택을 같은 데이터로 했다.
    DR-019는 "최종 평가 데이터를 모델 선택이나 하이퍼파라미터 조정에 사용하지 않는다"를
    요구한다. 이 스크립트는 그 조건을 지킨다.

절차 (순서를 바꾸면 안 된다):
    1. 분석 대상을 학습 70% / 홀드아웃 30%로 층화 분할 (SEED 고정)
    2. **학습 세트 안에서만** 교차검증으로 변수 구성을 고른다
    3. 고른 구성으로 학습 세트 전체에 적합
    4. **홀드아웃을 단 한 번** 평가한다
    5. SHAP으로 요인 기여를 낸다 (고정 요인 / 조절 가능 요인 분리)

사용법:
    uv run python -m ai_worker.risk_model.holdout
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ai_worker.risk_model.eda.swan_eda import build_cohort, label, load_baseline, load_followup

SEED = 20261124
SEED_BURNED = 20261124  # 1차 분할. 아래 "홀드아웃 사용 이력" 참조
HOLDOUT_FRAC = 0.30

# 홀드아웃 사용 이력 (DR-019 감사용 — 숨기지 않고 기록한다)
#
# 1차: SEED=20261124. 선택 규칙이 AUROC와 변수 개수만 보도록 되어 있어 "C5 LDL 단독"이
#      뽑혔고, 그 구성으로 홀드아웃을 1회 평가했다 (AUROC 0.796, 95% CI 0.749~0.844).
#      → 이 분할의 홀드아웃은 소진된 것으로 간주한다.
# 2차: SEED=20261125 (현재). 규칙을 고친 뒤 새로 분할해 평가한다.
#
# **평가 독립성의 한계 (리뷰 지적)**: 2차 분할은 1차와 같은 2,059명을 다시 나눈 것이므로
# 두 홀드아웃의 인원이 상당히 겹친다. 따라서 "완전한 평가 독립성이 확보됐다"고 말할 수
# 없다. 누출된 정보는 1차에서 본 "LDL 단독의 홀드아웃 AUROC" 한 값이고 그 구성은 후보에서
# 제외됐으나, 독립성이 부분적으로 훼손된 상태라는 점을 결과 해석에 반영해야 한다.
# 완전한 독립 평가를 원하면 새 코호트나 외부 데이터가 필요하다.
#
# 규칙을 왜 고쳤는가 (리뷰 지적 반영해 정정):
#   유효한 근거는 하나다 — REQ-PRED-009·010이 개인별 요인 설명을 요구하므로, 조절 가능
#   요인이 하나도 없는 구성(LDL 단독)은 성능이 같아도 서비스 모델 후보가 될 수 없다.
#   비교 기준선으로만 보고한다.
#
#   처음에는 "6장 기준에 보정이 들어 있는데 선택 규칙이 보정을 보지 않는다"를 근거로 들어
#   보정 최대 편차가 가장 작은 구성을 고르는 규칙으로 바꿨다. 그러나 그 지표가 분할 난수만
#   바꿔도 3.0% ↔ 10.7%로 뒤집히는 것을 확인해 폐기했다. 그래서 **최종 규칙에도 보정은
#   선택 조건으로 들어가지 않는다.** 보정은 참고 지표로 표에만 출력한다. 선택 조건은
#   ① 조절 가능 요인 포함 ② AUROC(반복 교차검증 평균)뿐이다.
SEED = 20261125

# 변수 구성 후보. 설계 v0.2 5.5절의 계수 방향 문제를 반영해 단계적으로 줄인다.
CANDIDATES: dict[str, list[str]] = {
    "C1 현행 B-": [
        "AGE0",
        "BMI0",
        "WAIST0",
        "peri",
        "HOTFLAS0",
        "NITESWE0",
        "smoke_now",
        "SPORTS0",
        "sfat_pct",
        "sbp",
        "LDLRESU0",
    ],
    "C2 BMI 제외": [
        "AGE0",
        "WAIST0",
        "peri",
        "HOTFLAS0",
        "NITESWE0",
        "smoke_now",
        "SPORTS0",
        "sfat_pct",
        "sbp",
        "LDLRESU0",
    ],
    "C3 +운동·포화지방 제외": ["AGE0", "WAIST0", "peri", "HOTFLAS0", "NITESWE0", "smoke_now", "sbp", "LDLRESU0"],
    "C4 최소 세트": ["AGE0", "WAIST0", "peri", "smoke_now", "LDLRESU0"],
    "C5 LDL 단독": ["LDLRESU0"],
}

# 서비스 모델 후보에서 제외하고 비교 기준선으로만 쓰는 구성.
# REQ-PRED-009·010이 개인별 요인 설명을 요구하므로, 조절 가능 요인이 없는 구성은
# 성능이 같더라도 서비스 모델이 될 수 없다.
REFERENCE_ONLY = {"C5 LDL 단독"}

# 데이터가 변수 구성을 구분하지 못할 때 고르는 구성 (선택 규칙 ③ 참조)
PRINCIPLED_CHOICE = "C3 +운동·포화지방 제외"

# 화면에서 "바꿀 수 있는 요인"으로 쓸 수 있는 변수 (설계 v0.2 5.5.3절)
MODIFIABLE = {"WAIST0", "smoke_now", "BMI0", "SPORTS0", "sfat_pct"}

LABELS = {
    "AGE0": "나이",
    "BMI0": "BMI",
    "WAIST0": "허리둘레",
    "peri": "이행기 초기",
    "HOTFLAS0": "홍조",
    "NITESWE0": "야간 발한",
    "smoke_now": "현재 흡연",
    "SPORTS0": "운동 빈도",
    "sfat_pct": "포화지방 비율",
    "sbp": "수축기 혈압",
    "LDLRESU0": "기저 LDL",
}

# 개인별 설명 예시에 쓰는 **가상 입력값**이다.
#
# 홀드아웃 실제 대상자를 뽑아 쓰지 않는다. SWAN은 ICPSR 제한 이용 데이터이고
# 이 레포지토리는 공개되어 있어, 개인 단위 건강정보와 발생 여부를 함께 싣는 것은
# 데이터 이용 조건에 어긋난다 (리뷰 지적, DR-015·DR-016).
#
# 아래 값은 폐경 이행기 여성의 범위 안에서 임의로 지은 반올림 수치다.
# 기여값은 실제 학습된 계수로 계산하므로 **모델의 거동은 사실 그대로**이고,
# 특정 참여자를 나타내지는 않는다. 가상이므로 실제 발생 여부도 없다.
SYNTHETIC_CASES: dict[str, dict[str, float]] = {
    "저위험·흡연": {
        "AGE0": 50,
        "BMI0": 22,
        "WAIST0": 70,
        "peri": 1,
        "HOTFLAS0": 2,
        "NITESWE0": 1,
        "smoke_now": 1,
        "SPORTS0": 3,
        "sfat_pct": 10,
        "sbp": 120,
        "LDLRESU0": 100,
    },
    "고위험·복부비만": {
        "AGE0": 48,
        "BMI0": 32,
        "WAIST0": 115,
        "peri": 0,
        "HOTFLAS0": 3,
        "NITESWE0": 2,
        "smoke_now": 0,
        "SPORTS0": 2,
        "sfat_pct": 14,
        "sbp": 130,
        "LDLRESU0": 150,
    },
}


def pipeline() -> object:
    """결측 대치 → 표준화 → 로지스틱 회귀. 설계 v0.2에서 선정한 구성."""
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=3000))


def calibration_bins(y: np.ndarray, p: np.ndarray, bins: int) -> tuple[pd.DataFrame, float, float]:
    """분위별 예측 평균과 실제 발생률, ECE, 최대 편차를 낸다."""
    q = pd.qcut(p, bins, labels=False, duplicates="drop")
    rows, gaps, sizes = [], [], []
    for g in np.unique(q):
        m = q == g
        pred, obs = p[m].mean(), y[m].mean()
        rows.append(
            {"분위": g + 1, "n": int(m.sum()), "예측": 100 * pred, "실제": 100 * obs, "차이": 100 * (obs - pred)}
        )
        gaps.append(abs(pred - obs))
        sizes.append(m.sum())
    ece = float(np.average(gaps, weights=sizes))
    return pd.DataFrame(rows), ece, float(max(gaps))


def recalibration_fit(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    """보정 절편과 기울기. 절편 0 / 기울기 1 이 완벽한 보정이다."""
    p = np.clip(p, 1e-6, 1 - 1e-6)
    logit = np.log(p / (1 - p)).reshape(-1, 1)
    fit = LogisticRegression().fit(logit, y)
    return float(fit.intercept_[0]), float(fit.coef_[0][0])


N_REPEATS = 20


def select_on_train(train: pd.DataFrame) -> dict[str, dict[str, tuple[float, float]]]:
    """학습 세트 안에서만 반복 교차검증해 변수 구성을 고른다. 홀드아웃은 건드리지 않는다.

    단일 5겹 교차검증은 이 표본 크기에서 매우 불안정하다. 분할 난수만 바꿔도
    보정 최대 편차가 3%에서 11%로 뒤집히는 것을 확인했다. 그래서 20회 반복해
    평균과 표준편차를 함께 본다.
    """
    print("\n=== 2단계: 학습 세트 내부 반복 교차검증으로 변수 구성 선택 ===")
    print(f"  학습 세트 n={len(train)}  발생={int(train.y.sum())} ({100 * train.y.mean():.1f}%)")
    print(f"  5겹 교차검증 × {N_REPEATS}회 반복, 평균 ± 표준편차")
    print("  ※ 홀드아웃은 이 단계에서 일절 사용하지 않는다 (DR-019)\n")
    y = train.y.astype(int).to_numpy()
    print(f"  {'후보':<24}{'변수':>5}{'AUROC':>16}{'AUPRC':>16}{'ECE':>15}{'최대편차':>16}")
    results: dict[str, dict[str, tuple[float, float]]] = {}
    for name, features in CANDIDATES.items():
        x = train[features].to_numpy(float)
        aurocs, auprcs, eces, worsts = [], [], [], []
        for rep in range(N_REPEATS):
            p = cross_val_predict(
                pipeline(),
                x,
                y,
                cv=StratifiedKFold(5, shuffle=True, random_state=1000 + rep),
                method="predict_proba",
            )[:, 1]
            _, ece, worst = calibration_bins(y, p, 10)
            aurocs.append(roc_auc_score(y, p))
            auprcs.append(average_precision_score(y, p))
            eces.append(ece)
            worsts.append(worst)
        results[name] = {
            "auroc": (float(np.mean(aurocs)), float(np.std(aurocs))),
            "auprc": (float(np.mean(auprcs)), float(np.std(auprcs))),
            "ece": (float(np.mean(eces)), float(np.std(eces))),
            "worst": (float(np.mean(worsts)), float(np.std(worsts))),
        }
        r = results[name]
        print(
            f"  {name:<24}{len(features):>5}"
            f"{r['auroc'][0]:>11.3f}±{r['auroc'][1]:.3f}"
            f"{r['auprc'][0]:>11.3f}±{r['auprc'][1]:.3f}"
            f"{100 * r['ece'][0]:>9.1f}±{100 * r['ece'][1]:.1f}%"
            f"{100 * r['worst'][0]:>10.1f}±{100 * r['worst'][1]:.1f}%"
        )
    return results


def judge_criteria(
    y: np.ndarray,
    p: np.ndarray,
    auroc: float,
    auroc_lo: float,
    worst10: float,
    worst5: float,
    rng: np.random.Generator,
) -> None:
    """설계 v0.2 6장 활용 기준을 판정하고 추정의 불확실성을 함께 보고한다.

    기준 단위는 **10분위**다 (v0.2 6장). 5분위는 분위당 인원이 많아 덜 흔들리므로
    보조 지표로만 쓴다. 판정을 느슨한 단위로 바꾸지 않는다.

    신뢰구간은 추정이 얼마나 흔들리는지를 보여주는 것이고, 하한이 기준 이하라는 사실이
    기준 충족을 뜻하지 않는다. 판정은 점추정으로 하고 신뢰구간은 함께 보고한다.
    """
    dev10, dev5 = [], []
    for _ in range(2000):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) > 1:
            _, _, w10 = calibration_bins(y[i], p[i], 10)
            _, _, w5 = calibration_bins(y[i], p[i], 5)
            dev10.append(w10)
            dev5.append(w5)

    print("\n  === 6장 활용 기준 판정 (기준 단위: 10분위) ===")
    ok_auroc = auroc >= 0.75
    ok_cal = worst10 <= 0.05
    print(
        f"    AUROC >= 0.75                     {'충족' if ok_auroc else '미충족'}  ({auroc:.3f}, CI 하한 {auroc_lo:.3f})"
    )
    print(f"    10분위 보정 편차 전 구간 5%p 이내  {'충족' if ok_cal else '미충족'}  (최대 {100 * worst10:.1f}%p)")
    print(f"    → 종합: {'충족' if ok_auroc and ok_cal else '미충족'}")
    print(f"    참고(기준 아님) 5분위 최대 편차: {100 * worst5:.1f}%p")

    print("\n  === 추정의 불확실성 (부트스트랩 2000회) ===")
    print("    ※ 신뢰구간 하한이 기준 이하라는 사실은 기준 충족을 뜻하지 않는다.")
    print("       판정은 위 점추정으로 하고, 아래는 추정이 얼마나 흔들리는지를 함께 보고한다.")
    for tag, arr, worst in (("10분위 (기준)", dev10, worst10), ("5분위 (보조)", dev5, worst5)):
        a = np.array(arr)
        dlo, dhi = np.percentile(a, [2.5, 97.5])
        print(
            f"    {tag:<14} 점추정 {100 * worst:5.1f}%p   95% CI {100 * dlo:5.1f} ~ {100 * dhi:5.1f}%p"
            f"   5%p 초과 비율 {100 * np.mean(a > 0.05):3.0f}%"
        )

    d10 = np.array(dev10)
    if np.percentile(d10, 2.5) > 0.05:
        print("    → 10분위 기준: 신뢰구간 하한도 5%p를 넘는다. 미충족이 안정적으로 관찰된다.")
    elif np.percentile(d10, 97.5) < 0.05:
        print("    → 10분위 기준: 신뢰구간 상한도 5%p 아래다. 충족이 안정적으로 관찰된다.")
    else:
        print("    → 10분위 기준: 신뢰구간이 5%p를 포함한다. 추정이 흔들리는 구간이므로")
        print("       점추정 판정과 함께 표본 크기 한계를 보고한다.")


def criterion_feasibility(p: np.ndarray, n_sim: int = 5000) -> None:
    """이 표본 크기에서 5%p 기준이 달성 가능한 기준인지 확인한다.

    예측확률 p를 참값으로 두고 y ~ Bernoulli(p)를 생성하면 그 모델은 **정의상 완벽히
    보정된 모델**이다. 그런 모델에서도 분위별 관측 발생률은 표본 오차로 흔들리므로
    최대 편차가 0이 되지 않는다. 그 분포를 보면 기준이 측정 노이즈보다 큰지 작은지
    판단할 수 있다.
    """
    rng = np.random.default_rng(777)
    print("\n  === 기준의 달성 가능성 (완벽 보정 모델 시뮬레이션) ===")
    print(f"    예측확률을 참값으로 두고 y ~ Bernoulli(p)를 {n_sim}회 생성 (n={len(p)})")
    for bins in (10, 5):
        worsts, eces = [], []
        for _ in range(n_sim):
            y_sim = (rng.random(len(p)) < p).astype(int)
            if len(np.unique(y_sim)) < 2:
                continue
            _, e, w = calibration_bins(y_sim, p, bins)
            worsts.append(w)
            eces.append(e)
        w, e = np.array(worsts), np.array(eces)
        print(
            f"    {bins:2d}분위  최대 편차 중앙값 {100 * np.median(w):4.1f}%p"
            f"  90% 구간 {100 * np.percentile(w, 5):4.1f}~{100 * np.percentile(w, 95):4.1f}%p"
            f"  5%p 이내일 확률 {100 * np.mean(w <= 0.05):4.1f}%"
        )
        print(
            f"            ECE 중앙값 {100 * np.median(e):3.1f}%"
            f"  90분위 {100 * np.percentile(e, 90):3.1f}%"
            f"  95분위 {100 * np.percentile(e, 95):3.1f}%"
            f"  99분위 {100 * np.percentile(e, 99):3.1f}%"
            f"  최대 {100 * e.max():3.1f}%"
        )
        print(
            f"            ECE 5% 이내일 확률 {100 * np.mean(e <= 0.05):4.1f}%"
            f"   → 기준을 ECE 5%로 두면 완벽 모델을 {100 * np.mean(e > 0.05):.1f}% 확률로 탈락시킨다"
        )
    print("    ※ 완벽히 보정된 모델도 5%p 기준을 넘는다면, 그 기준은 이 표본 크기에서")
    print("       모델의 품질을 판정하지 못한다. 측정 노이즈가 기준보다 크기 때문이다.")
    print("    ※ ECE 분위수는 기준값 설정의 근거로 쓴다. 완벽 모델이 그 값을 넘을 확률이")
    print("       곧 '제대로 보정된 모델을 잘못 탈락시킬 확률'(1종 오류)이다 (리뷰 요청).")


def evaluate_holdout(train: pd.DataFrame, hold: pd.DataFrame, features: list[str], name: str) -> None:
    """홀드아웃을 단 한 번 평가한다. 이 함수는 한 번만 호출한다."""
    print(f"\n{'=' * 70}")
    print(f"=== 4단계: 홀드아웃 1회 평가 — {name} ({len(features)}개 변수) ===")
    print(f"{'=' * 70}")

    model = pipeline().fit(train[features].to_numpy(float), train.y.astype(int))
    y = hold.y.astype(int).to_numpy()
    p = model.predict_proba(hold[features].to_numpy(float))[:, 1]

    auroc, auprc = roc_auc_score(y, p), average_precision_score(y, p)
    rng = np.random.default_rng(SEED)
    boots = []
    for _ in range(2000):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) > 1:
            boots.append(roc_auc_score(y[i], p[i]))
    lo, hi = np.percentile(boots, [2.5, 97.5])

    sens = recall_score(y, p >= np.quantile(p, 0.8))
    intercept, slope = recalibration_fit(y, p)
    # 설계 v0.2 6장 기준은 **10분위** 최대 편차 5%p 이내다. 판정은 10분위로 한다.
    # 5분위는 분위당 인원이 많아 추정이 덜 흔들리므로 보조 지표로만 함께 본다.
    table10, ece10, worst10 = calibration_bins(y, p, 10)
    table5, ece5, worst5 = calibration_bins(y, p, 5)

    print(f"\n  홀드아웃 n={len(hold)}  발생={int(y.sum())} ({100 * y.mean():.1f}%)")
    print(f"\n  AUROC           {auroc:.3f}   95% CI [{lo:.3f}, {hi:.3f}]")
    print(f"  AUPRC           {auprc:.3f}")
    print(f"  민감도@상위20%    {sens:.3f}")
    print(
        f"  Brier           {brier_score_loss(y, p):.4f}   (무정보 기준선 {brier_score_loss(y, np.full_like(y, y.mean(), dtype=float)):.4f})"
    )
    print(f"  보정 절편        {intercept:+.3f}   (0이 이상)")
    print(f"  보정 기울기      {slope:.3f}   (1이 이상)")
    print(f"  ECE (10분위, 기준) {100 * ece10:.1f}%")
    print(f"  최대 편차 (10분위, 기준) {100 * worst10:.1f}%p")
    print(f"  ECE (5분위, 보조)  {100 * ece5:.1f}%")
    print(f"  최대 편차 (5분위, 보조)  {100 * worst5:.1f}%p")

    print(f"\n  보정 10분위 — 활용 기준의 판정 단위. 분위당 약 {len(hold) // 10}명.")
    print(f"    {'분위':>4}{'n':>6}{'예측':>9}{'실제':>9}{'차이':>10}")
    for _, r in table10.iterrows():
        print(f"    {int(r['분위']):>4}{int(r['n']):>6}{r['예측']:>8.1f}%{r['실제']:>8.1f}%{r['차이']:>+9.1f}%p")

    print("\n  보정 5분위 — 보조. 분위당 인원이 많아 덜 흔들리지만 기준 단위는 아니다.")
    print(f"    {'분위':>4}{'n':>6}{'예측':>9}{'실제':>9}{'차이':>10}")
    for _, r in table5.iterrows():
        print(f"    {int(r['분위']):>4}{int(r['n']):>6}{r['예측']:>8.1f}%{r['실제']:>8.1f}%{r['차이']:>+9.1f}%p")

    print("\n  기저 LDL 구간별 (홀드아웃)")
    for low, high in ((0, 100), (100, 130), (130, 145), (145, 160)):
        m = ((hold.LDLRESU0 >= low) & (hold.LDLRESU0 < high)).to_numpy()
        n, k = int(m.sum()), int(y[m].sum())
        if n == 0:
            continue
        a = roc_auc_score(y[m], p[m]) if 0 < k < n else float("nan")
        print(
            f"    LDL {low:3d}~{high:3d}  n={n:4d}  발생={k:3d} ({100 * k / n:4.1f}%)  AUROC={a:.3f}  예측평균={100 * p[m].mean():4.1f}%"
        )

    judge_criteria(y, p, auroc, lo, worst10, worst5, rng)
    criterion_feasibility(p)


def compare_with_baseline(train: pd.DataFrame, hold: pd.DataFrame, features: list[str], name: str) -> None:
    """선택된 모델과 LDL 단독 기준선의 보정을 홀드아웃에서 비교한다 (DR-008).

    리뷰 요청: "홀드아웃에서도 B- 모델의 구간별 보정 이점이 유지되는지 확인".
    학습 세트 교차검증에서는 B-의 10분위 최대 편차가 LDL 단독보다 작았다
    (설계 v0.2 5.4절: 1.5%p 대 3.8%p). 독립 표본에서 그 차이가 남는지 본다.

    주의: 이 비교는 **이미 확정된 모델에 대한 보고**다. 이 결과를 보고 최종 모델을
    바꾸면 홀드아웃이 모델 선택에 쓰인 것이 되어 DR-019를 위반한다. 그 경우 새
    홀드아웃을 떼야 한다.
    """
    print(f"\n{'=' * 70}")
    print("=== 4-2단계: 선택 모델 vs LDL 단독 기준선 보정 비교 (DR-008) ===")
    print(f"{'=' * 70}")

    y = hold.y.astype(int).to_numpy()
    sets = {name: features, "LDL 단독": ["LDLRESU0"]}
    probs, stats = {}, {}
    for tag, fs in sets.items():
        model = pipeline().fit(train[fs].to_numpy(float), train.y.astype(int))
        p = model.predict_proba(hold[fs].to_numpy(float))[:, 1]
        probs[tag] = p
        _, ece10, worst10 = calibration_bins(y, p, 10)
        _, ece5, worst5 = calibration_bins(y, p, 5)
        stats[tag] = {
            "auroc": roc_auc_score(y, p),
            "brier": brier_score_loss(y, p),
            "ece10": ece10,
            "worst10": worst10,
            "ece5": ece5,
            "worst5": worst5,
        }

    print(f"\n  {'모델':<24}{'AUROC':>8}{'Brier':>9}{'ECE10':>8}{'최대10':>9}{'ECE5':>8}{'최대5':>8}")
    for tag, s in stats.items():
        print(
            f"  {tag:<24}{s['auroc']:>8.3f}{s['brier']:>9.4f}"
            f"{100 * s['ece10']:>7.1f}%{100 * s['worst10']:>8.1f}%"
            f"{100 * s['ece5']:>7.1f}%{100 * s['worst5']:>7.1f}%"
        )

    # 차이의 불확실성. "이점이 유지되는가"는 차이의 신뢰구간이 0을 포함하는지로 답한다.
    rng = np.random.default_rng(SEED + 1)
    diffs10, diffs5 = [], []
    pa, pb = probs[name], probs["LDL 단독"]
    for _ in range(2000):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) < 2:
            continue
        _, _, wa10 = calibration_bins(y[i], pa[i], 10)
        _, _, wb10 = calibration_bins(y[i], pb[i], 10)
        _, _, wa5 = calibration_bins(y[i], pa[i], 5)
        _, _, wb5 = calibration_bins(y[i], pb[i], 5)
        diffs10.append(wa10 - wb10)
        diffs5.append(wa5 - wb5)

    # 점추정 차이와 부트스트랩 평균 차이를 함께 낸다. 최대값은 비선형 통계량이라
    # 두 값이 일치하지 않고 부호까지 다를 수 있다. 둘을 같은 것으로 쓰면 안 된다.
    print("\n  === 최대 편차 차이 (선택 모델 − LDL 단독). 음수면 선택 모델이 더 좋다 ===")
    for tag, arr, direct in (
        ("10분위", diffs10, stats[name]["worst10"] - stats["LDL 단독"]["worst10"]),
        ("5분위", diffs5, stats[name]["worst5"] - stats["LDL 단독"]["worst5"]),
    ):
        arr = np.array(arr)
        lo, hi = np.percentile(arr, [2.5, 97.5])
        better = float(np.mean(arr < 0))
        verdict = "이점 확인" if hi < 0 else ("열세 확인" if lo > 0 else "판정 불가 (CI가 0을 포함)")
        print(
            f"    {tag}  점추정 차이 {100 * direct:+.1f}%p   부트스트랩 평균 차이 {100 * arr.mean():+.1f}%p"
            f"   95% CI [{100 * lo:+.1f}, {100 * hi:+.1f}]%p   더 좋을 확률 {100 * better:.0f}%"
        )
        print(f"           → {verdict}")
    print("    ※ 최대값은 비선형 통계량이라 점추정 차이와 부트스트랩 평균 차이가 일치하지")
    print("       않으며 부호도 다를 수 있다. 어느 쪽도 단독으로 우열의 근거가 되지 못한다.")

    print("\n  === 학습 세트 교차검증과의 대조 ===")
    print("    설계 v0.2 5.4절(전체 데이터 교차검증): B- 최대 편차 1.5%p vs LDL 단독 3.8%p")
    print(
        f"    본 검증 홀드아웃(10분위): {name} {100 * stats[name]['worst10']:.1f}%p vs LDL 단독 {100 * stats['LDL 단독']['worst10']:.1f}%p"
    )
    print("    ※ 홀드아웃은 분위당 62명이라 편차 추정이 매우 불안정하다. 위 신뢰구간을 함께 볼 것.")


def linear_shap(coef: np.ndarray, x: np.ndarray, background_mean: np.ndarray) -> np.ndarray:
    """선형 모형의 SHAP 기여값. 근사가 아니라 정확한 해다.

    로지스틱 회귀의 로그오즈는 변수의 선형 결합이므로, 각 변수의 Shapley 값은
    순서와 무관하게 phi_j = coef_j * (x_j - E[x_j]) 하나로 결정된다.

    `shap` 라이브러리의 LinearExplainer와 같은 값을 낸다 (오차 0.0 확인).
    numba·llvmlite를 끌고 오는 `shap` 의존성을 피하기 위해 직접 계산한다.
    모델을 비선형(부스팅 등)으로 바꾸면 이 식은 더 이상 쓸 수 없고 `shap`이 필요하다.
    """
    return coef * (x - background_mean)


def shap_report(train: pd.DataFrame, hold: pd.DataFrame, features: list[str]) -> None:
    """요인 기여를 고정 요인 / 조절 가능 요인으로 나눠 낸다 (설계 v0.2 10-1절)."""
    model = pipeline().fit(train[features].to_numpy(float), train.y.astype(int))
    imputer, scaler, logreg = model[0], model[1], model[2]
    xt_train = scaler.transform(imputer.transform(train[features].to_numpy(float)))
    xt_hold = scaler.transform(imputer.transform(hold[features].to_numpy(float)))

    # 배경 분포는 학습 세트 전체를 쓴다.
    values = linear_shap(logreg.coef_[0], xt_hold, xt_train.mean(axis=0))

    print("\n=== 5단계: SHAP 요인 기여 (홀드아웃 평균 절대 기여) ===")
    mean_abs = np.abs(values).mean(axis=0)
    order = np.argsort(-mean_abs)
    print(f"  {'변수':<14}{'평균 |SHAP|':>12}{'구분':>12}")
    for i in order:
        kind = "조절 가능" if features[i] in MODIFIABLE else "고정"
        print(f"  {LABELS.get(features[i], features[i]):<14}{mean_abs[i]:>12.3f}{kind:>12}")

    fixed_idx = [i for i, f in enumerate(features) if f not in MODIFIABLE]
    mod_idx = [i for i, f in enumerate(features) if f in MODIFIABLE]
    fixed_share = mean_abs[fixed_idx].sum()
    mod_share = mean_abs[mod_idx].sum()
    total = fixed_share + mod_share
    print(f"\n  고정 요인 합계      {fixed_share:.3f} ({100 * fixed_share / total:.1f}%)")
    print(f"  조절 가능 요인 합계  {mod_share:.3f} ({100 * mod_share / total:.1f}%)")
    print("  ※ 조절 가능 요인 비중이 작으므로 화면에서는 두 묶음을 분리해 표시해야 한다 (10-1절)")

    synthetic_examples(model, features, xt_train.mean(axis=0))


def synthetic_examples(model: object, features: list[str], background: np.ndarray) -> None:
    """가상 입력값으로 개인별 설명 화면을 예시한다.

    실제 참여자를 쓰지 않는 이유는 SYNTHETIC_CASES 주석 참조.
    기여값은 학습된 계수로 계산하므로 모델의 거동 자체는 사실 그대로다.
    """
    imputer, scaler, logreg = model[0], model[1], model[2]
    print("\n=== 개인별 설명 예시 (가상 입력값) ===")
    print("  ※ 실제 SWAN 참여자가 아니다. 임의로 지은 값이며 실제 발생 여부도 없다.")
    for tag, case in SYNTHETIC_CASES.items():
        x = np.array([[float(case[f]) for f in features]])
        p = model.predict_proba(x)[0, 1]
        v = linear_shap(logreg.coef_[0], scaler.transform(imputer.transform(x)), background)[0]
        print(f"\n  [{tag}] 5년 발생 확률 {100 * p:.1f}%  (가상 사례)")
        for j in sorted(range(len(features)), key=lambda j: -abs(v[j])):
            kind = "조절 가능" if features[j] in MODIFIABLE else "고정"
            label = LABELS.get(features[j], features[j])
            print(f"    {label:<12} 값 {case[features[j]]:>7.1f}   기여 {v[j]:+.3f}   {kind}")


def main() -> None:
    baseline = load_baseline()
    followup = load_followup()
    cohort = build_cohort(baseline, followup)
    d = label(followup, cohort, window=5, include_med=True)

    print(f"\n=== 1단계: 학습 / 홀드아웃 분할 (SEED={SEED}) ===")
    train, hold = train_test_split(d, test_size=HOLDOUT_FRAC, stratify=d.y, random_state=SEED)
    print(f"  전체     n={len(d):5d}  발생={int(d.y.sum()):4d} ({100 * d.y.mean():.1f}%)")
    print(f"  학습 70% n={len(train):5d}  발생={int(train.y.sum()):4d} ({100 * train.y.mean():.1f}%)")
    print(f"  홀드아웃 30% n={len(hold):5d}  발생={int(hold.y.sum()):4d} ({100 * hold.y.mean():.1f}%)")

    results = select_on_train(train)

    # 선택 규칙 (홀드아웃을 보기 전에 확정한다).
    # **보정 지표는 선택 조건이 아니다** — 분할마다 뒤집혀 신뢰할 수 없다(상단 주석 참조).
    # 아래 표에 함께 출력하지만 판단 근거로는 쓰지 않는다.
    #   ① 서비스 모델 후보만 — 조절 가능 요인이 하나 이상 (REQ-PRED-010).
    #      LDL 단독은 요인 설명이 불가능하므로 비교 기준선으로만 쓴다.
    #   ② 후보들의 AUROC 평균 차이가 반복 간 표준편차보다 작으면
    #      **데이터가 구성을 구분하지 못한다**고 판단한다.
    #   ③ 그 경우 지표로 고르지 않고, 문서화된 해석 가능성 요건으로 고른다:
    #      설계 v0.2 5.5절에서 계수 방향이 임상과 반대이거나 다중공선성으로 부호가
    #      뒤집히는 변수(BMI·운동 빈도·포화지방 비율)를 제외한 구성 = C3.
    #      근거는 SR-027(인과 해석 금지)과 REQ-PRED-010(변경 가능 요인 구분)이다.
    #   ④ 구분이 된다면 AUROC 평균이 가장 높은 구성을 고른다.
    service = {n: v for n, v in results.items() if n not in REFERENCE_ONLY}
    means = {n: v["auroc"][0] for n, v in service.items()}
    sds = {n: v["auroc"][1] for n, v in service.items()}
    spread = max(means.values()) - min(means.values())
    typical_sd = float(np.mean(list(sds.values())))

    print("\n  === 선택 판단 ===")
    print(f"  후보 간 AUROC 평균 최대 차이  {spread:.4f}")
    print(f"  반복 간 평균 표준편차         {typical_sd:.4f}")
    if spread < typical_sd:
        chosen_name = PRINCIPLED_CHOICE
        print("  → 차이가 표준편차보다 작다. **데이터가 변수 구성을 구분하지 못한다.**")
        print("  → 지표로 고르지 않고 해석 가능성 요건으로 고른다 (설계 v0.2 5.5절):")
        print("     BMI(다중공선성 부호 반전) · 운동 빈도(방향 반대) · 포화지방 비율(방향 반대) 제외")
    else:
        chosen_name = max(means, key=means.get)
        print("  → 차이가 표준편차보다 크다. AUROC 평균 최고 구성을 선택한다.")
    chosen = CANDIDATES[chosen_name]
    print(f"\n  → 선택: **{chosen_name}** ({len(chosen)}개 변수)")
    print(f"     {', '.join(LABELS.get(c, c) for c in chosen)}")
    mod = [c for c in chosen if c in MODIFIABLE]
    print(f"     이 중 조절 가능 요인: {', '.join(LABELS.get(c, c) for c in mod) if mod else '없음'}")

    print("\n=== 3단계: 선택된 구성으로 학습 세트 전체에 적합 ===")
    model = pipeline().fit(train[chosen].to_numpy(float), train.y.astype(int))
    coef = model[-1].coef_[0]
    print("  표준화 계수 (학습 세트 기준)")
    for i in np.argsort(-np.abs(coef)):
        print(f"    {LABELS.get(chosen[i], chosen[i]):<12}{coef[i]:>+8.3f}")

    evaluate_holdout(train, hold, chosen, chosen_name)
    compare_with_baseline(train, hold, chosen, chosen_name)
    shap_report(train, hold, chosen)


if __name__ == "__main__":
    main()
