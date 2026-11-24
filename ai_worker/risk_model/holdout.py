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
from ai_worker.risk_model.eda.swan_eda import build_cohort, label, load_baseline, load_followup
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

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
# 규칙을 왜 고쳤는가: 설계 v0.2 6장은 활용 기준을 "AUROC >= 0.75 **그리고** 보정 편차
# 전 구간 5%p 이내"로 정의한다. 그런데 선택 규칙이 보정을 보지 않았다. 기준과 선택
# 규칙이 어긋나 있었던 것이고, 홀드아웃 결과를 보고 규칙을 바꾼 것이 아니다.
# 또한 REQ-PRED-009·010은 개인별 요인 설명을 요구하므로, 조절 가능 요인이 하나도 없는
# 구성(LDL 단독)은 서비스 모델 후보가 될 수 없다. 비교 기준선으로만 보고한다.
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
    _, ece5, worst5 = calibration_bins(y, p, 5)

    print(f"\n  홀드아웃 n={len(hold)}  발생={int(y.sum())} ({100 * y.mean():.1f}%)")
    print(f"\n  AUROC           {auroc:.3f}   95% CI [{lo:.3f}, {hi:.3f}]")
    print(f"  AUPRC           {auprc:.3f}")
    print(f"  민감도@상위20%    {sens:.3f}")
    print(
        f"  Brier           {brier_score_loss(y, p):.4f}   (무정보 기준선 {brier_score_loss(y, np.full_like(y, y.mean(), dtype=float)):.4f})"
    )
    print(f"  보정 절편        {intercept:+.3f}   (0이 이상)")
    print(f"  보정 기울기      {slope:.3f}   (1이 이상)")
    print(f"  ECE (5분위)     {100 * ece5:.1f}%")
    print(f"  최대 편차 (5분위) {100 * worst5:.1f}%p")

    print("\n  보정 5분위 — 홀드아웃 n이 작아 분위당 인원이 적다. 편차 해석에 주의.")
    table, _, _ = calibration_bins(y, p, 5)
    print(f"    {'분위':>4}{'n':>6}{'예측':>9}{'실제':>9}{'차이':>10}")
    for _, r in table.iterrows():
        print(f"    {int(r['분위']):>4}{int(r['n']):>6}{r['예측']:>8.1f}%{r['실제']:>8.1f}%{r['차이']:>+9.1f}%p")

    print(f"\n  참고: 10분위 (분위당 약 {len(hold) // 10}명, 매우 불안정)")
    _, ece10, worst10 = calibration_bins(y, p, 10)
    print(f"    ECE {100 * ece10:.1f}%   최대 편차 {100 * worst10:.1f}%p")

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

    # 보정 편차 자체의 불확실성. 5%p 기준을 이 표본으로 판정할 수 있는지 본다.
    dev_boots = []
    for _ in range(2000):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) > 1:
            _, _, w = calibration_bins(y[i], p[i], 5)
            dev_boots.append(w)
    dlo, dhi = np.percentile(dev_boots, [2.5, 97.5])
    over_rate = float(np.mean(np.array(dev_boots) > 0.05))

    print("\n  === 6장 활용 기준 판정 ===")
    ok_auroc = auroc >= 0.75
    ok_cal = worst5 <= 0.05
    print(f"    AUROC >= 0.75                 {'충족' if ok_auroc else '미충족'}  ({auroc:.3f}, CI 하한 {lo:.3f})")
    print(f"    보정 편차 전 구간 5%p 이내      {'충족' if ok_cal else '미충족'}  (최대 {100 * worst5:.1f}%p)")
    print(f"    → 종합: {'충족' if ok_auroc and ok_cal else '미충족'}")

    print("\n  === 이 판정을 믿을 수 있는가 (보정 편차의 불확실성) ===")
    print(f"    최대 편차 점추정    {100 * worst5:.1f}%p")
    print(f"    부트스트랩 95% CI   {100 * dlo:.1f}%p ~ {100 * dhi:.1f}%p")
    print(f"    5%p를 넘길 확률     {100 * over_rate:.0f}%")
    if dlo <= 0.05 <= dhi:
        print("    → 신뢰구간이 5%p를 포함한다. **이 표본 크기로는 5%p 기준의 충족 여부를")
        print("       판정할 수 없다.** 점추정이 5.1%p로 기준을 넘긴 것은 노이즈와 구분되지 않는다.")
        print("       기준 수치를 유지하려면 더 큰 홀드아웃이, 이 표본을 쓰려면 측정 가능한")
        print("       기준(예: 교차검증 ECE 또는 편차 신뢰구간 상한)으로 바꿔야 한다.")


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

    print("\n  === 최대 편차 차이 (선택 모델 − LDL 단독). 음수면 선택 모델이 더 좋다 ===")
    for tag, arr in (("10분위", diffs10), ("5분위", diffs5)):
        arr = np.array(arr)
        lo, hi = np.percentile(arr, [2.5, 97.5])
        better = float(np.mean(arr < 0))
        verdict = "이점 확인" if hi < 0 else ("열세 확인" if lo > 0 else "**판정 불가 (CI가 0을 포함)**")
        print(
            f"    {tag}  차이 {100 * arr.mean():+.1f}%p  95% CI [{100 * lo:+.1f}, {100 * hi:+.1f}]%p  "
            f"더 좋을 확률 {100 * better:.0f}%  → {verdict}"
        )

    print("\n  === 학습 세트 교차검증과의 대조 ===")
    print("    설계 v0.2 5.4절(전체 데이터 교차검증): B- 최대 편차 1.5%p vs LDL 단독 3.8%p")
    print(
        f"    본 검증 홀드아웃(10분위): {name} {100 * stats[name]['worst10']:.1f}%p vs LDL 단독 {100 * stats['LDL 단독']['worst10']:.1f}%p"
    )
    print("    ※ 홀드아웃은 분위당 62명이라 편차 추정이 매우 불안정하다. 위 신뢰구간을 함께 볼 것.")


def shap_report(train: pd.DataFrame, hold: pd.DataFrame, features: list[str]) -> None:
    """SHAP 기여를 고정 요인 / 조절 가능 요인으로 나눠 낸다 (설계 v0.2 10-1절)."""
    import shap

    model = pipeline().fit(train[features].to_numpy(float), train.y.astype(int))
    imputer, scaler, logreg = model[0], model[1], model[2]
    xt_train = scaler.transform(imputer.transform(train[features].to_numpy(float)))
    xt_hold = scaler.transform(imputer.transform(hold[features].to_numpy(float)))

    # 배경 표본을 전부 쓴다. 기본값(100개 추출)이면 기여도에 추출 노이즈가 섞인다.
    masker = shap.maskers.Independent(xt_train, max_samples=len(xt_train))
    explainer = shap.LinearExplainer(logreg, masker)
    values = explainer.shap_values(xt_hold)

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

    print("\n=== 개인별 설명 예시 (홀드아웃에서 예측확률 분위별 1명) ===")
    p = model.predict_proba(hold[features].to_numpy(float))[:, 1]
    for tag, target in (("낮음", 0.10), ("중간", 0.35), ("높음", 0.65)):
        i = int(np.argmin(np.abs(p - target)))
        print(f"\n  [{tag}] 5년 발생 확률 {100 * p[i]:.1f}%  (실제 {'발생' if hold.y.to_numpy()[i] else '미발생'})")
        contrib = sorted(
            ((features[j], values[i, j]) for j in range(len(features))),
            key=lambda t: -abs(t[1]),
        )
        for f, v in contrib:
            kind = "조절 가능" if f in MODIFIABLE else "고정"
            raw = hold[f].to_numpy()[i]
            raw_txt = "결측" if pd.isna(raw) else f"{raw:.1f}"
            print(f"    {LABELS.get(f, f):<12} 값 {raw_txt:>7}   기여 {v:+.3f}   {kind}")


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

    # 선택 규칙 (홀드아웃을 보기 전에 확정한다):
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
