# 🤝 WELLOOP 협업 규칙 (CONTRIBUTING)

> 1조 WELLOOP(웰루프) · 🔁 건강한 습관이 반복되는 선순환
> 이 문서는 팀 협업 규칙이에요. 바뀌면 PR로 수정해요.

---

## 1. 폴더 구조

OZ 템플릿 구조를 기본으로 하고, 팀에서 필요한 폴더를 추가했어요.

```
welloop/
├── app/                  # 백엔드 (FastAPI)
│   ├── apis/             #  주소(URL)별 요청 받는 곳
│   ├── services/         #  실제 로직 (위험도 요청, 챌린지 처리)
│   ├── repositories/     #  DB 읽고 쓰기
│   ├── models/           #  DB 테이블 정의
│   ├── dtos/             #  요청·응답 데이터 형식
│   ├── core/             #  설정, 인증(JWT)
│   └── tests/
├── ai_worker/            # AI 담당 (예측 모델 추론, LLM 코치 문장)
│   └── tasks/
├── frontend/             # 화면 (팀에서 기술 정하고 추가)
├── notebooks/            # 데이터 분석·모델 실험 (ipynb)
├── docs/
│   ├── meetings/         #  회의록 (YYYY-MM-DD.md)
│   ├── planning/         #  요구사항 정의서, ERD, API 명세서, 와이어프레임 링크
│   └── troubleshooting/  #  문제 → 원인 → 해결 기록
├── infra/ · scripts/ · envs/   # 템플릿 그대로 (배포·설정)
└── .github/              # PR 템플릿, 커밋 템플릿
```

- 층을 나누는 이유: **각자 담당 폴더가 겹치지 않게** 하고, 평가 기준의 "계층 구조·의존성 분리"를 지키기 위해서예요.
- 데이터 원본(csv 등)은 용량이 커서 **레포에 올리지 않아요.** `.gitignore`에 `data/`를 넣고, 받는 방법만 README에 적어요.

## 2. 브랜치 규칙

| 브랜치 | 용도 | 예시 |
|---|---|---|
| `main` | 배포용. **직접 push 금지** | |
| `dev` | 기능이 모이는 곳 (develop을 줄여 dev). **직접 push 금지** | 11/23 템플릿 올린 직후 생성 |
| `feat/영역-기능` | 기능 개발 (feature를 줄여 feat) | `feat/be-auth`, `feat/ai-risk-model`, `feat/fe-dashboard` |
| `fix/영역-내용` | 버그 수정 | `fix/be-login-error` |
| `docs/내용` | 문서·회의록 | `docs/meeting-1117` |

- 영역 약어: `be` 백엔드 · `ai` AI · `fe` 프론트 · `infra` 배포
- 이슈 번호를 앞에 붙이면 추적이 쉬워요. 예: `feat/12-be-auth`

## 3. 작업 순서 (기능 하나마다)

1. **GitHub Issue 만들기**: 무엇을 할지 적고 담당자 지정
2. **dev에서 브랜치 따기**: 작업 전 `git pull origin dev` 필수
3. **커밋**: 아래 커밋 컨벤션대로
4. **PR 올리기**: base는 `dev`, 본문에 `Closes #이슈번호`
5. **리뷰 1명 Approve → Merge → 브랜치 삭제**

```bash
git checkout dev
git pull origin dev
git checkout -b feat/be-auth
# ... 개발 ...
git add 파일
git commit                         # 커밋 템플릿 사용
git pull --rebase origin dev   # 내 브랜치 최신화 (feat 브랜치라 rebase OK)
git push origin feat/be-auth
# → GitHub에서 PR (base: dev)
```

> 이미 push한 내 브랜치를 rebase했다면 그냥 push가 거절돼요. 이때만 `git push --force-with-lease origin feat/be-auth`를 써요. (아래 6장 참고)

## 4. 커밋 컨벤션

형식: `<타입>: <요약>` (이모지는 쓰지 않아요)

| 타입 | 언제 쓰나 |
|---|---|
| feat | 새 기능 추가 |
| fix | 버그 수정 |
| docs | 문서·회의록 |
| refactor | 기능 변화 없이 코드 정리 |
| test | 테스트 추가·수정 |
| chore | 설정·패키지 등 자잘한 수정 |

예: `feat: 로그인 API 추가`, `fix: 위험도 계산 오류 수정`, `docs: 11/17 회의록`

- 요약은 한글로, 무엇을 했는지 한 줄로 써요.
- 이전에 이모지를 넣은 커밋은 그대로 둬요. (기록을 고치려면 강제 push가 필요해서 하지 않아요)

## 5. PR 규칙

- PR 하나에 **기능 하나만**. 작게 자주 올려요.
- **본인이 올린 PR은 본인이 Merge하지 않아요.** 리뷰어가 Approve 후 Merge해요.
- Merge는 팀장만 하는 게 아니에요. 승인한 리뷰어 누구나 할 수 있어요.
- 리뷰어는 **해당 파트 담당자**로 지정해요. (파트별 리뷰어는 R&R 확정 후 이 문서에 추가)
- 목적은 꼼꼼한 검사보다 "무엇이 바뀌었는지 서로 아는 것"이에요.
- 24시간 안에 리뷰가 없으면 데일리 스크럼에서 이야기해요.
- 회의록은 `docs/meetings/YYYY-MM-DD.md`로 매일 PR을 올려요. (첫 회의록만 빈 레포라 main에 직접 올림)

## 6. 절대 금지 🚫

### 공유 브랜치(`main`·`dev`)에서 금지
- 직접 push, 강제 push(`push -f`), `reset --hard`, `rebase`
  → 되돌릴 땐 `git revert`

### 내 feat 브랜치에서는 허용
| 작업 | 허용 여부 |
|---|---|
| `git pull --rebase origin dev`, `git rebase --continue` | ✅ 허용 |
| 강제 push | ✅ 허용, 단 **`git push --force-with-lease`만** 사용 (`push -f` X) |

- `--force-with-lease`는 "내가 마지막으로 받은 뒤에 다른 사람이 이 브랜치에 올린 게 없을 때만" 덮어써요. 누가 같은 브랜치에 커밋을 올렸다면 거절해서, 남의 작업을 실수로 지우는 걸 막아줘요.
- 다른 사람과 같이 쓰는 브랜치라면 rebase·강제 push 전에 먼저 말해요.

### API 키·`.env`·`.pem`
- 커밋하거나 채팅·AI에 붙여넣지 않아요.
- **실수로 노출됐다면 순서대로:**
  1. **즉시 해당 키를 폐기·재발급**해요. 지워도 이미 유출된 것이라, 키를 무효로 만드는 게 가장 먼저예요.
     - 운영진이 준 팀 키(LLM API 등)는 직접 폐기할 수 없으니 **바로 운영진에게 알려 폐기·재발급을 요청**해요.
     - 내가 발급한 키(공공데이터포털 등)는 직접 폐기·재발급해요.
  2. **운영진과 팀에 공유**해요. (어디에, 언제 노출됐는지)
  3. 새 키는 `.env`에만 넣고 `.gitignore` 확인
- 다른 사람 담당 폴더를 말없이 크게 수정하기 → 이슈나 스크럼에서 먼저 공유

## 7. 충돌이 나면 (내 feat 브랜치에서 `git pull --rebase` 중)

1. `<<<<<<<` ~ `=======`(dev 쪽) / `=======` ~ `>>>>>>>`(내 쪽) 중 남길 코드만 남기고 표시 줄 삭제
2. `git add 파일` → `git rebase --continue`
3. 헷갈리면 `git rebase --abort` 후 해당 코드 작성자·조교님께 문의

## 8. GitHub 설정 (팀장)

Settings → Rules(또는 Branches)에서 `main`·`dev`에:
- **Require a pull request before merging** + 승인 1명
- **Block force pushes**

## ⚠️ 11/23 템플릿 세팅 때 주의

레포에 이미 커밋(회의록, 이 문서)이 있어서, 템플릿을 push하기 전에 먼저 합쳐야 해요.

```bash
git pull origin main --allow-unrelated-histories
```

push가 거절돼도 **`push -f`는 절대 쓰지 않아요.** 레포에 있던 회의록이 지워져요.

또, OZ 템플릿의 GitHub Actions(자동 테스트) 설정 파일(`.github/workflows/`)에 `develop`이라는 브랜치 이름이 들어 있으면 `dev`로 바꿔야 자동 테스트가 돌아가요. 템플릿을 받은 날 함께 확인해요.
