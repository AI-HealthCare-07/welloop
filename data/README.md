# data/ (로컬 전용)

이 폴더의 파일은 **GitHub에 올라가지 않아요.** (`data/.gitignore`가 README와 자기 자신만 남기고 전부 제외)

| 폴더 | 내용 |
|---|---|
| `raw/` | 국민건강영양조사 기본DB `.sav` (2021~2024), Kaggle 공개 데이터 |
| `interim/` | 연도 통합·응답 코드 정리본 |
| `processed/` | 학습용 데이터 (parquet). 합성 데이터도 여기에 생성 |

## 받는 방법
- 국민건강영양조사: 질병관리청 국민건강영양조사 누리집에서 회원가입 → 원시자료 이용 서약 후 기본DB(SPSS) 내려받기 → `raw/`에 `HN21_ALL.sav` ~ `HN24_ALL.sav`로 둡니다.
- 승인 전이거나 원자료가 없을 때: 합성 데이터로 개발합니다.

```bash
python -m ai_worker.risk_model.data.synthetic --n 3000 --out data/processed/synthetic_cohort.parquet
```

원자료를 디스코드·채팅·AI에 올리지 않아요.
