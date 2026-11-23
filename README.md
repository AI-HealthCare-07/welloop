# WELLOOP

> 폐경 이행기 여성의 고LDL콜레스테롤혈증 예방을 돕는 AI 기반 맞춤형 건강관리 서비스

서비스 기획 내용은 [서비스 기획 개요](docs/service_overview.md)에 있어요.

## 기술 스택

| 영역 | 사용 기술 |
|---|---|
| 언어·패키지 | Python 3.13, uv |
| 백엔드 | FastAPI, Tortoise ORM, Aerich(마이그레이션), Pydantic |
| AI 워커 | scikit-learn, PyTorch(CPU), sentence-transformers |
| DB·캐시 | MySQL 8.0, Redis |
| 인프라 | Docker Compose, Nginx(리버스 프록시) |
| 품질 관리 | Ruff, Mypy, Pytest, GitHub Actions |

## 폴더 구조

```text
welloop/
├── app/                # 백엔드 (FastAPI)
│   ├── apis/v1/        #   URL별 요청을 받는 라우터
│   ├── services/       #   비즈니스 로직
│   ├── repositories/   #   DB 읽기·쓰기
│   ├── models/         #   DB 테이블 정의 (Tortoise)
│   ├── dtos/           #   요청·응답 데이터 형식
│   ├── core/           #   설정, DB·마이그레이션, JWT, 검증기
│   └── tests/
├── ai_worker/          # AI 워커 (모델 추론, LLM 코치 문장)
├── infra/              # 운영용 compose, Nginx 설정
├── scripts/            # 배포·CI 스크립트
├── envs/               # 환경 변수 예시 파일 (example.*.env만 커밋)
├── data/               # 데이터 원자료 (로컬 전용, 커밋 안 함)
├── docs/               # 기획·회의록 (planning/, meetings/)
├── docker-compose.yml  # 로컬 개발용 전체 스택
└── pyproject.toml      # 의존성 (uv)
```

## 개발 환경 세팅 (WSL)

**사전 준비**
- WSL2 (Ubuntu)
- Docker Desktop: Settings → Resources → WSL Integration에서 사용하는 배포판을 켜 주세요.
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- 레포는 WSL 파일 시스템(`~/...`)에 clone해 주세요. `/mnt/c/...` 아래에 두면 느리고 파일 감지가 잘 안 돼요.

**1. 의존성 설치**

```bash
uv sync --python 3.13 --all-groups --frozen
```

**2. 환경 변수 파일 만들기**

```bash
cp envs/example.local.env envs/.local.env
```

`envs/.local.env`에서 `DB_HOST=localhost`를 `DB_HOST=mysql`로 바꿔 주세요.
컨테이너 안에서 `localhost`는 MySQL이 아니라 자기 자신을 가리켜서, 바꾸지 않으면 API가 DB에 연결하지 못해요.

**3. 루트 `.env`에 연결하기**

docker compose와 앱 설정은 루트의 `.env`를 읽어요. 실제 파일은 `envs/.local.env` 하나만 두고, 루트에는 링크를 걸어요.

```bash
ln -s envs/.local.env .env
```

**4. 전체 스택 실행**

```bash
docker compose up -d --build
docker compose exec fastapi uv run --no-sync aerich upgrade   # 처음 한 번: DB 테이블 생성
```

- API 문서: http://localhost/api/docs
- 상태 확인: `docker compose ps`에서 mysql과 redis가 `healthy`이면 정상이에요.
- 지금은 ai-worker가 `Restarting`으로 보여요. 템플릿 기본 명령이 `echo`라서 그렇고, AI 워커를 구현하면 해결돼요.

**코드 검사·테스트**

```bash
uv run ruff check . && uv run ruff format . --check   # CI lint와 같아요
./scripts/ci/run_test.sh                               # mysql 컨테이너가 떠 있어야 해요
```

## 브랜치·PR 규칙

자세한 내용은 [CONTRIBUTING.md](CONTRIBUTING.md)와 [PR_GUIDE.md](PR_GUIDE.md)에 있어요.

- `main`(배포)과 `dev`(통합)에는 **직접 push할 수 없어요.** 모든 변경은 PR로 올리고, 1명 이상 승인을 받아야 머지돼요.
- `dev`에서 브랜치를 만들어요: `feat/영역-기능`, `fix/영역-내용`, `docs/내용` (영역: `be`, `ai`, `fe`, `infra`)
- 커밋 형식: `<타입>: <요약>` (feat, fix, docs, refactor, test, chore)
- PR 하나에는 작업 하나만 담아요. base는 `dev`로 하고, 본인 PR은 본인이 머지하지 않아요.
- 공유 브랜치에서 `push -f`, `reset --hard`, `rebase`는 금지예요. 되돌릴 때는 `git revert`를 써요.

## 보안 규칙

레포는 **공개 상태**예요.

- `.env`, `envs/.local.env`, `envs/.prod.env`, API 키, `.pem` 파일은 커밋하지 않아요. 채팅이나 AI에도 붙여넣지 않아요.
- 국민건강영양조사 등 데이터 원자료는 `data/`에만 두고 커밋하지 않아요. `.gitignore`로 막혀 있어요. 받는 방법은 [data/README.md](data/README.md)에 있어요.
- `envs/example.*.env`의 값은 공개된 예시예요. 운영 환경에서는 반드시 새 값으로 바꿔요.
- 키가 노출됐다면 **바로 폐기·재발급**하고 팀에 알려 주세요. 자세한 절차는 [CONTRIBUTING.md](CONTRIBUTING.md) 6장에 있어요.
