# risk_model — 3대 대사질환 위험 신호 예측 모듈

- 담당: 김도엽 (서브 홍시윤)
- 설계: [`docs/planning/WELLOOP_AI모델링_설계_v0.1.md`](../../docs/planning/WELLOOP_AI모델링_설계_v0.1.md)
- 관련 요구사항: REQ-006·007·008 / NFR-006·007·009·015

## 지금 상태: 기준 모델로 `predict_risk()` 동작 (합성 데이터)

| 단계 | 내용 | 상태 |
|---|---|---|
| 0 | 폴더·입력 계약·합성 데이터·테스트 | ✅ |
| 1 | 국건영 전처리·라벨·미진단자 데이터셋 | 예정 |
| 2 | 기준 모델 + `predict_risk()` 1차 동작 | ✅ 합성 데이터 (`risk-v0.0-synth`) · 국건영 학습은 단계 1 뒤 |
| 3 | 비교 모델·성능 평가 | 예정 |
| 4 | 최종 모델 선정·경계값 초안 | 예정 |
| 5·6 | 추론 모듈 완성·테스트·연동 문서 | 예정 |

레포의 `risk-v0.0-synth`는 **합성 데이터로 만든 연동용 모델**이에요. 점수·지표에 의미가 없습니다.
응답의 `data_source`가 `SYNTHETIC`이면 화면에 데모 표시를 해 주세요.

## 백엔드에서 쓰는 법

```python
from ai_worker.tasks.risk import predict_risk, RiskInputError

try:
    out = predict_risk(input_snapshot, diseases=["DIABETES", "DYSLIPIDEMIA"])  # 관리 중 질환은 빼고 호출
except RiskInputError as e:
    ...  # e.errors = {"age": "필수값 누락"} → 400
# out = {"model_version", "data_source", "results": [{"disease_type", "risk_score", "major_factors"}], "imputed_fields"}
```

- `risk_level`·종합 점수·`is_managed`는 백엔드에서 계산해요 (API 명세서 03 구역).
- "만약에"는 `input_snapshot` 값을 바꿔 한 번 더 부르면 됩니다.
- 모델 버전은 환경변수 `RISK_MODEL_VERSION`으로 고정할 수 있어요. 없으면 실제 데이터 모델 → 합성 모델 순으로 고릅니다.

## 실행 (레포 루트에서)

```bash
pip install -r ai_worker/risk_model/requirements.txt
python -m ai_worker.risk_model.data.synthetic --n 3000 --out data/processed/synthetic_cohort.parquet
python -m ai_worker.risk_model.train --data data/processed/synthetic_cohort.parquet --version risk-v0.0-synth   # 모델 다시 만들 때만
python -m pytest ai_worker/risk_model/tests -q
```

## 파일

| 파일 | 역할 |
|---|---|
| `feature_spec.yaml` | 예측 입력 계약 (ERD 컬럼명, 범위, 국건영 변수 대응, 입력 금지 필드) |
| `spec.py` | 계약 읽기, `validate_input()` |
| `errors.py` | `RiskInputError` (백엔드는 400으로 변환) |
| `config.py` | 경로·시드·질환 목록·데이터 출처 표시 |
| `features.py` · `train.py` · `predict.py` · `registry.py` | 변수 변환 · 기준 모델 학습 · 추론 · 모델 저장(JSON) |
| `artifacts/risk-v0.0-synth/` | 합성 데이터 모델 (계수 JSON + 메타데이터) |
| `data/synthetic.py` | 합성 데이터 생성 (개발·테스트 전용, `data_source=SYNTHETIC`) |
| `../tasks/risk.py` | 백엔드가 부르는 `predict_risk()` |

## 지켜야 할 것
- 원자료는 `data/`에만 두고 레포에 올리지 않아요 (`data/.gitignore`).
- 혈압·혈당·검진 수치·진단·복약 정보는 예측 입력에 넣지 않아요 (라벨 누수 방지).
- 합성 데이터로 만든 결과는 성능 근거로 쓰지 않아요.
