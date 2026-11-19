# WELLOOP AI 모델링 설계 v0.1

- 작성: 김도엽 (AI 모델링 주 담당) · 2026-11-19
- 기준 문서: 요구사항 v1.3 (REQ-006·007·008, NFR-006·007·009·015), ERD v1.3, API 명세서 03 구역
- 범위: 국건영 전처리 → 라벨 → 미진단자 데이터셋 → 기준·비교 모델 → 선정 → 저장·버전 → `predict_risk()`
- 범위 밖 (백엔드 담당): `is_managed` 판단, `risk_level` 변환, 종합 점수, 재계산 시점, DB 저장, API

---

## 1. 설계 원칙

1. **독립 실행**: 백엔드·DB·템플릿 없이 이 모듈만으로 학습·평가·추론·테스트가 돌아간다.
2. **템플릿과 충돌하지 않는다**: 11/23 전에는 아래 3곳에만 파일을 만든다. 루트 설정 파일(`.gitignore`, `pyproject.toml`, `docker-compose.yml` 등)은 만들지 않는다.
3. **원자료는 레포에 없다** (NFR-015): `data/` 안에 자체 `.gitignore`를 두어 폴더째 제외한다.
4. **실제·합성 데이터를 섞지 않는다**: 모든 산출물(데이터셋·모델·리포트)에 `data_source`를 기록하고, 합성 데이터로 만든 모델은 버전 이름에 `-synth`가 붙는다.
5. **같은 입력 → 같은 출력** (NFR-007): 추론에 난수·외부 호출·LLM이 없다.
6. **성능은 숨기지 않는다**: 낮은 지표도 그대로 기록하고, 화면 표현은 "위험 신호"로 유지한다.

## 2. 폴더 구조

```
welloop/
├── ai_worker/
│   ├── tasks/
│   │   └── risk.py                  # 백엔드가 부르는 얇은 진입점: predict_risk()
│   └── risk_model/                  # AI 모델링 패키지 (전부 여기 안에)
│       ├── README.md                #  실행 방법 · 백엔드 연동 안내
│       ├── requirements.txt         #  이 패키지만의 의존성 (템플릿 설정과 분리)
│       ├── feature_spec.yaml        #  입력 계약: 필드·타입·범위·국건영 변수 매핑
│       ├── config.py                #  경로·시드·모델 버전
│       ├── data/
│       │   ├── load_knhanes.py      #  연도별 .sav 읽기 → 변수 통합
│       │   ├── clean.py             #  응답 코드(8·9·99 등) → 결측, 단위·범위 정리
│       │   ├── labels.py            #  3대 질환 라벨 + 진단·복약 여부
│       │   ├── cohort.py            #  45세 이상 · 검진 완료 · 미진단자 추출
│       │   └── synthetic.py         #  스키마가 같은 합성 데이터 생성 (개발·테스트용)
│       ├── features.py              #  input_snapshot → 모델 입력 (학습·추론 공용)
│       ├── baselines.py             #  FINDRISC, KoGES형 로지스틱, 단순 점수식
│       ├── train.py                 #  학습 (모델·질환 선택)
│       ├── evaluate.py              #  지표·보정·리포트
│       ├── explain.py               #  major_factors (개인별 기여도 Top3)
│       ├── registry.py              #  모델 저장·불러오기·버전
│       ├── predict.py               #  추론 본체
│       ├── artifacts/
│       │   └── risk-v0.1/           #  model_*.joblib · metadata.json · model_card.md
│       └── tests/                   #  pytest (합성 데이터만 사용)
├── notebooks/
│   ├── 01_knhanes_변수확인.ipynb
│   ├── 02_라벨_코호트.ipynb
│   ├── 03_baseline.ipynb
│   └── 04_모델비교.ipynb
├── data/                            # 로컬 전용 (자체 .gitignore로 전부 제외)
│   ├── raw/        # HN21~24 .sav, Kaggle csv
│   ├── interim/    # 통합·정리본
│   └── processed/  # 학습용 parquet
└── docs/planning/
    ├── WELLOOP_AI모델링_설계_v0.1.md   # 이 문서
    └── WELLOOP_모델실험기록.md          # 실험 표 (계속 누적)
```

- 템플릿에 `ai_worker/tasks/`가 이미 있으면 `risk.py` 파일 하나만 추가된다. 나머지는 새 하위 폴더라 겹치지 않는다.
- 노트북은 탐색용이고, 재현해야 하는 로직은 전부 `risk_model/`의 `.py`에 둔다.

## 3. 데이터 흐름

```
[로컬] raw (.sav 4개 연도)
   → load_knhanes → clean → labels → cohort
   → processed/cohort_{disease}.parquet   (data_source: KNHANES | KAGGLE_NHIS | SYNTHETIC)
   → train / evaluate
   → artifacts/risk-vX.Y/ (모델 + metadata.json + model_card.md)
                         ↓ (레포에 커밋)
[서비스] 백엔드 서비스 계층 → ai_worker/tasks/risk.predict_risk(input_snapshot)
   → features → 모델 3개 → explain → 결과 dict
```

### 데이터 승인 대응

| 상태 | 사용할 데이터 | 할 수 있는 일 |
|---|---|---|
| 승인 전 | 합성 데이터(`synthetic.py`) + Kaggle 국민건강보험 공개 데이터 | 파이프라인·학습 코드·추론·테스트 전부 완성, `risk-v0.0-synth` 모델로 백엔드 연동 |
| 승인 후 | 국건영 2021~2024 (로컬) | 실제 학습·평가, `risk-v0.1` 이후 버전 |

## 4. 입력 계약 (`feature_spec.yaml`)

`input_snapshot`의 키는 **ERD 컬럼명 그대로**다. 03 공통 규칙의 "예측 입력"과 같다.

| 필드 | 출처 (ERD) | 국건영 변수 | 모델 입력 | 필수 |
|---|---|---|---|---|
| `age` | users.birth_date에서 계산 | age | ✅ | 필수 |
| `gender` | users.gender | sex | ✅ | 필수 |
| `height` · `weight` → BMI | questionnaires / health_logs 최신 | HE_ht · HE_wt · HE_BMI | ✅ | 필수 |
| `waist_size` | questionnaires / health_logs 최신 | HE_wc | ✅ | 필수 |
| `smoking_status` | questionnaires | BS3_1 · BS1_1 | ✅ | 필수 |
| `drinking_days_per_week` · `drinks_per_occasion` | questionnaires | BD1_11 · BD2_1 | ✅ | 선택 |
| `activity_days_per_week` · `activity_minutes_per_day` | questionnaires | pa_aerobic 등 | ✅ | 선택 |
| `strength_days_per_week` | questionnaires | BE5_1 | ✅ | 선택 |
| `veg_freq` · `fruit_freq` · `breakfast_freq` | questionnaires | LS_VEG1 · LS_FRUIT · L_BR_FQ | ✅ | 선택 |
| `sleep_hours` | 체크인 14일 평균 또는 문진 | BP16_* | ✅ | 선택 |
| `family_htn` · `family_dm` · `family_dl` | questionnaires | HE_HPfh · HE_DMfh · HE_HLfh 1~3 | ✅ | 선택 (UNKNOWN 허용) |
| `menopause_status` | questionnaires (여성만) | LW_ms | ✅ | 선택 |
| 짠·단 음식, 정제 탄수화물, 수면 불편, 금연 의향, 운동 제한 | questionnaires | 문항 없음 | ❌ 추천용 | - |
| 혈압·혈당·검진 수치 | health_logs · checkup_records | 라벨 정의에 사용 | ❌ **입력 금지** | - |

- 선택 필드가 없으면 학습 때 정한 값으로 채우고, 채운 필드 이름을 결과에 알려 준다.
- 문진 선택지(예: "주 2일")와 국건영 응답 코드의 대응은 `feature_spec.yaml`에 표로 적는다. **02 문진 필드가 확정돼야 최종본이 된다.**

## 5. 출력 계약 (`predict_risk`)

```python
# ai_worker/tasks/risk.py
def predict_risk(input_snapshot: dict, diseases: list[str] | None = None) -> dict:
    ...
```

```json
{
  "model_version": "risk-v0.1",
  "data_source": "KNHANES",
  "results": [
    { "disease_type": "HYPERTENSION", "risk_score": 0.31, "major_factors": ["waist_size", "age", "family_htn"] },
    { "disease_type": "DIABETES",     "risk_score": 0.62, "major_factors": ["waist_size", "family_dm", "activity_days_per_week"] },
    { "disease_type": "DYSLIPIDEMIA", "risk_score": 0.18, "major_factors": ["waist_size"] }
  ],
  "imputed_fields": ["sleep_hours"]
}
```

| 항목 | 규칙 |
|---|---|
| `risk_score` | 보정된 확률 0~1, 소수 4자리 (ERD `decimal(5,4)`). 높을수록 위험 신호가 크다 |
| `major_factors` | 그 사람의 점수를 **올린** 요인 상위 3개 이하, ERD 컬럼명. 올린 요인이 없으면 빈 배열 |
| `diseases` | 생략하면 3개 전부. 백엔드가 관리 중인 질환을 빼고 싶으면 목록으로 지정 |
| 오류 | 필수 필드 누락·범위 초과는 `RiskInputError`(누락 필드 목록 포함). 백엔드가 400으로 변환 |
| 하지 않는 일 | `is_managed`, `risk_level`, 종합 점수, 하루 1회 제한, DB 저장 |

"만약에" 시뮬레이션(No 11)은 백엔드가 `input_snapshot` 값을 바꿔 `predict_risk`를 한 번 더 부르면 된다. 별도 함수가 필요 없다.

## 6. 모델링 설계

| 항목 | 내용 |
|---|---|
| 대상 | 국건영 2021~2024, 45세 이상, 검진·혈액검사 완료 (15,061명 확인) |
| 학습 집단 | 질환별 **미진단자** (의사 진단 없음 + 해당 약 복용 없음) |
| 라벨 (NFR-009) | 고혈압: 수축기≥140 또는 이완기≥90 / 당뇨: 공복혈당≥126 또는 HbA1c≥6.5 / 이상지질혈증: TC≥240 · LDL≥160 · TG≥200 · HDL<40 중 하나 |
| 분할 | 2021~2023 학습(5겹 교차검증) · **2024 테스트**(연도 분리로 누수 방지) |
| 기준 모델 | 당뇨: FINDRISC 점수 / 고혈압: KoGES 변수(혈압 제외) 로지스틱 / 이상지질혈증: 나이·성별·BMI·허리둘레 로지스틱 |
| 비교 모델 | 로지스틱 회귀(전체 변수), Random Forest, LightGBM |
| 지표 | AUROC, AUPRC, Recall·Precision·F1(경계값별), Brier 점수·보정 곡선 |
| 불균형 | 가중치(`class_weight`) 우선. 학습 후 확률 보정(isotonic 또는 sigmoid) |
| 외부 검증 | Kaggle 국민건강보험 데이터로 공통 변수 모델 확인 (참고용) |
| 비교 실험 | 전체 학습 vs 미진단자 학습 (회의 결정대로 기록) |
| 선정 기준 | ① 테스트 AUPRC ② 보정 ③ 기준 모델 대비 개선. AUROC 차이가 0.01 미만이면 **단순한 모델(로지스틱)** 선택 |
| 경계값 | 주의·높음 시작 확률 **초안**을 질환별로 제안 → 백엔드 `risk_thresholds`에 등록 (관리자가 수정 가능) |

### 미리 알려 둘 한계
- 비침습 변수만 쓰므로 AUROC 0.65~0.75 수준을 예상한다 (Kaggle 사전 확인 0.63~0.68).
- 2021년은 LDL 직접 측정이 12%뿐이다 → LDL 기준 처리 방법을 단계 1에서 정하고 기록한다.
- 수면 문항은 연도별로 형식이 다르다(시각 vs 시간) → 시간 단위로 통일.
- 응답 코드 해석은 이용지침서 확인 전까지 추정이다.

## 7. 모델 저장·버전

- 이름: `risk-v{주}.{부}` (예: `risk-v0.1`). 합성 데이터 모델은 `risk-v0.0-synth`.
- 버전 폴더 1개 = 질환별 모델 3개 + `metadata.json` + `model_card.md`
- `metadata.json`: 버전, 학습일, `data_source`, 학습 연도·인원, 변수 목록, 지표, 제안 경계값, 라이브러리 버전, git 커밋
- 서비스가 쓸 버전은 `config.py`의 기본값 또는 환경변수 `RISK_MODEL_VERSION`으로 고른다.
- 모델 파일은 크기가 작아 레포에 커밋한다 (원자료·개인 행 데이터는 들어 있지 않음). **팀 확인 필요.**

## 8. 단계별 산출물과 완료 기준

| 단계 | 기간(목표) | 산출물 | 완료 기준 |
|---|---|---|---|
| **0. 뼈대** | 11/19~20 | 폴더, `requirements.txt`, `feature_spec.yaml` 초안, `synthetic.py`, `data/.gitignore`, 이 설계서 | 새 환경에서 설치 → 합성 데이터 생성 → 빈 테스트 통과. 원자료가 git에 잡히지 않음 |
| **1. 전처리** | ~11/27 | `load_knhanes` · `clean` · `labels` · `cohort`, 노트북 01·02, 코호트 요약표 | 명령 한 번으로 raw → processed 생성. 인원·유병률이 기존 확인값(15,061명 등)과 일치하거나 차이 이유가 기록됨. 응답 코드 처리가 이용지침서와 대조됨. 라벨·코호트 단위 테스트 통과 |
| **2. 기준 모델** | ~12/1 | `baselines.py`, `train.py`, `evaluate.py`, 노트북 03, **`risk-v0.0` 연동용 모델** | 질환 3개 기준 모델의 CV·테스트 지표가 실험 기록에 있음. 이 모델로 `predict_risk()`가 동작(백엔드가 먼저 붙일 수 있음) |
| **3. 비교·평가** | ~12/8 | 비교 모델 3종, 보정, 전체 vs 미진단자 실험, 노트북 04 | 모델×질환 지표 표 완성(AUROC·AUPRC·Recall·Brier). 누수 점검 항목 통과. 보정 곡선 저장 |
| **4. 최종 선정** | ~12/11 | `risk-v0.1` 아티팩트, `model_card.md`, 경계값 초안 | 선정 이유가 기준에 따라 문서화됨. 경계값 초안을 백엔드·관리자 담당에게 전달 |
| **5. 추론 모듈** | ~12/11 (2와 병행) | `features.py` · `explain.py` · `registry.py` · `predict.py`, `tasks/risk.py` | 출력 계약 준수. 같은 입력 100회 → 같은 출력. 1건 추론 100ms 이내(로컬). 잘못된 입력에 `RiskInputError` |
| **6. 테스트·연동 문서** | ~12/15 | `tests/`, `README.md`(연동 안내·예시 입출력), 백엔드와 통합 확인 | pytest 전부 통과(원자료 없이). 백엔드 담당이 README만 보고 호출 성공. 03 명세 예시 JSON과 필드 일치 |

- 단계 5는 2와 함께 시작한다. **기준 모델로 먼저 연결하고, 모델만 교체**하는 방식이라 백엔드 일정(W3 핵심 루프 ①)을 막지 않는다.

### 누수 점검 항목 (단계 3)
- [ ] 입력 변수에 혈압·혈당·지질 수치나 진단·복약 정보가 없다
- [ ] 결측 대체·스케일링·보정이 학습 데이터에서만 맞춰진다
- [ ] 테스트 연도(2024)가 학습·튜닝에 쓰이지 않았다
- [ ] 같은 사람이 학습·테스트에 동시에 없다 (국건영은 연도별 독립 표본, ID 확인)

## 9. 브랜치·PR 계획

| PR | 브랜치 | 내용 |
|---|---|---|
| 1 | `docs/ai-model-design` | 이 설계서 |
| 2 | `feat/ai-risk-skeleton` | 단계 0 |
| 3 | `feat/ai-risk-preprocess` | 단계 1 |
| 4 | `feat/ai-risk-baseline` | 단계 2 + 추론 모듈 1차 |
| 5 | `feat/ai-risk-compare` | 단계 3·4 |
| 6 | `feat/ai-risk-integration` | 단계 5·6 |

리뷰어: 1순위 홍시윤, 2순위 송승환 (R&R).

## 10. 팀 확인이 필요한 것

| # | 내용 | 확인할 사람 |
|---|---|---|
| 1 | 국건영 사용 승인 결과 (조교님) | 엄태은 |
| 2 | `predict_risk()` 입출력 계약(4·5장) 동의 | 송승환 |
| 3 | 02 문진 필드·선택지 확정 (snake_case·ERD Enum) → `feature_spec.yaml` 반영 | 송승환 |
| 4 | 모델 파일을 레포에 커밋해도 되는지 | 엄태은 · 이명석 |
| 5 | 종합 점수 규칙 채택 여부 (03 대조 결과 1) — 모델은 질환별 점수만 제공 | 팀 전체 |
| 6 | 11/23 템플릿의 `ai_worker/` 구조·의존성 관리 방식 → 필요하면 `requirements.txt` 통합 | 이명석 |
