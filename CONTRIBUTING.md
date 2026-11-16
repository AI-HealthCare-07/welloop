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
| `develop` | 기능이 모이는 곳. **직접 push 금지** | 11/23 템플릿 올린 직후 생성 |
| `feature/영역-기능` | 기능 개발 | `feature/be-auth`, `feature/ai-risk-model`, `feature/fe-dashboard` |
| `fix/영역-내용` | 버그 수정 | `fix/be-login-error` |
| `docs/내용` | 문서·회의록 | `docs/meeting-1117` |

- 영역 약어: `be` 백엔드 · `ai` AI · `fe` 프론트 · `infra` 배포
- 이슈 번호를 앞에 붙이면 추적이 쉬워요. 예: `feature/12-be-auth`

## 3. 작업 순서 (기능 하나마다)

1. **GitHub Issue 만들기**: 무엇을 할지 적고 담당자 지정
2. **develop에서 브랜치 따기**: 작업 전 `git pull origin develop` 필수
3. **커밋**: 아래 커밋 컨벤션대로
4. **PR 올리기**: base는 `develop`, 본문에 `Closes #이슈번호`
5. **리뷰 1명 Approve → Merge → 브랜치 삭제**

```bash
git checkout develop
git pull origin develop
git checkout -b feature/be-auth
# ... 개발 ...
git add 파일
git commit                         # 커밋 템플릿 사용
git pull --rebase origin develop   # 내 브랜치 최신화
git push origin feature/be-auth
# → GitHub에서 PR (base: develop)
```

## 4. 커밋 컨벤션

형식: `<이모지> <타입>: <요약>`

| 이모지 | 타입 | 의미 |
|---|---|---|
| ✨ | feat | 새 기능 |
| 🐛 | fix | 버그 수정 |
| 💡 | chore | 자잘한 수정 |
| 📝 | docs | 문서 |
| 🚚 | build | 빌드 |
| ✅ | test | 테스트 |
| ♻️ | refactor | 리팩터링 |
| 🚑 | hotfix | 긴급 수정 |

예: `✨ feat: 로그인 API 추가`, `📝 docs: 11/17 회의록`

## 5. PR 규칙

- PR 하나에 **기능 하나만**. 작게 자주 올려요.
- 리뷰어는 다른 영역 사람 1명도 OK. 목적은 "무엇이 바뀌었는지 서로 아는 것"이에요.
- 24시간 안에 리뷰가 없으면 데일리 스크럼에서 이야기해요.
- 회의록은 `docs/meetings/YYYY-MM-DD.md`로 매일 PR을 올려요. (첫 회의록만 빈 레포라 main에 직접 올림)

## 6. 절대 금지 🚫

- `main`·`develop`에 직접 push, `push -f`(강제 push), `reset --hard`, `rebase`
  → 되돌릴 땐 `git revert`. 강제 push는 내 feature 브랜치에서만.
- **API 키·`.env`·`.pem` 파일을 커밋하거나 채팅·AI에 붙여넣기**
  → 실수로 올렸다면 지워도 유출된 것이에요. 즉시 운영진에게 공유해요.
- 다른 사람 담당 폴더를 말없이 크게 수정하기 → 이슈나 스크럼에서 먼저 공유

## 7. 충돌이 나면

1. `<<<<<<<` ~ `=======`(develop 쪽) / `=======` ~ `>>>>>>>`(내 쪽) 중 남길 코드만 남기고 표시 줄 삭제
2. `git add 파일` → `git rebase --continue`
3. 헷갈리면 `git rebase --abort` 후 해당 코드 작성자·조교님께 문의

## 8. GitHub 설정 (팀장)

Settings → Rules(또는 Branches)에서 `main`·`develop`에:
- **Require a pull request before merging** + 승인 1명
- **Block force pushes**

## ⚠️ 11/23 템플릿 세팅 때 주의

레포에 이미 커밋(회의록, 이 문서)이 있어서, 템플릿을 push하기 전에 먼저 합쳐야 해요.

```bash
git pull origin main --allow-unrelated-histories
```

push가 거절돼도 **`push -f`는 절대 쓰지 않아요.** 레포에 있던 회의록이 지워져요.
