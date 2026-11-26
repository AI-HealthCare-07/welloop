# data/ (로컬 전용)

이 폴더의 파일은 **GitHub에 올라가지 않아요.** (`data/.gitignore`가 README와 자기 자신만 남기고 전부 제외)

원자료를 레포·디스코드·채팅·외부 AI 서비스에 올리지 않아요 (DR-015·DR-016).

| 폴더 | 내용 |
|---|---|
| `raw/swan/` | **SWAN 종단 코호트** ICPSR 자료 `.sav` — 예측 모델의 **핵심 학습 데이터** (DR-001) |
| `raw/knhanes/`, `raw/nhanes/` | 국건영·NHANES — 국내외 여성 특성 **비교용 참고 자료** (DR-002). 학습에 쓰지 않아요 |
| `interim/` | 회차 통합·응답 코드 정리본 |
| `processed/` | 학습용 데이터 (parquet) |

> **SWAN이 학습 데이터고, 국건영·NHANES는 참고 자료예요.** 둘을 섞지 않아요 (DR-002). 2026-11-24에 주제가 "국건영 기반 3질환 현재 위험"에서 "SWAN 기반 고LDL 5년 발생 위험"으로 바뀌었어요.

## SWAN 받는 방법

1. [ICPSR 시리즈 253](https://www.icpsr.umich.edu/web/ICPSR/series/253)에서 회원가입 후 이용 약관에 동의해요
2. 아래 자료를 **SPSS 형식**으로 내려받아 `data/raw/swan/ICPSR_<번호>/`에 그대로 둬요

| 회차 | ICPSR | 지질 검사 | 모델 1 | 모델 2 |
|---|---|---|---|---|
| V0 (기저) | 28762 | O | O | — |
| V1 | 29221 | O | O | O |
| V2 | 29401 | × | — | O |
| V3 | 29701 | O | O | O |
| V4 | 30142 | O | O | O |
| V5 | 30501 | O | O | O |
| V6 | 31181 | O | O | O |
| V7 | 31901 | O | O | O |
| V8 | 32122 | × | — | O |
| V9 | 32721 | × | — | O |
| V10 | 32961 | × | — | O |

배치 예시예요.

```
data/raw/swan/ICPSR_28762/DS0001/28762-0001-Data.sav
data/raw/swan/ICPSR_29221/...
```

**모델 1(폐경 전·이행기 초기)만 재현하려면 7개로 충분해요** — V0·V1·V3·V4·V5·V6·V7. 지질 검사가 있는 회차예요.

**모델 2(이행기 후기·폐경 후)에는 11개가 다 필요해요.** V2·V8·V9·V10에 지질 검사는 없지만 `STATUS`(폐경 단계)와 `AGE`가 있어서, 단계에 처음 들어선 방문을 찾고 추적 창을 실제 경과 연수로 재는 데 써요.

## 실행

```bash
# 모델 1 — 코호트 구축부터 변수 선정까지
uv run python -m ai_worker.risk_model.eda.swan_eda

# 모델 1 — 홀드아웃 검증 (1회 평가, 이미 소진)
uv run python -m ai_worker.risk_model.holdout

# 모델 2 — 코호트 규모 확인
uv run python -m ai_worker.risk_model.model2_cohort
```

자료가 없으면 스크립트가 파일을 못 찾고 멈춰요. 합성 데이터 생성기는 국건영 기준으로 만들었던 것이라 주제 변경과 함께 제거됐어요.

## 참고 문서

- [AI 모델링 설계 v0.2](../docs/planning/WELLOOP_AI모델링_설계_v0.2.md) — 모델 1
- [AI 모델링 설계 v0.3](../docs/planning/WELLOOP_AI모델링_설계_v0.3.md) — 모델 2 코호트
- [홀드아웃 검증 결과](../docs/planning/WELLOOP_홀드아웃_검증_결과.md)
- [문진·SWAN 변수 매핑표](../docs/planning/WELLOOP_문진_SWAN변수_매핑표.md)
