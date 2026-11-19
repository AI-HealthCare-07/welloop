"""설정. 비밀값은 환경변수(.env)로만 받아요 (NFR-004)."""
import os
import secrets

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/welloop_demo.db")
# JWT_SECRET이 없으면 실행할 때마다 새로 만들어요 (개발용: 서버를 다시 켜면 로그인이 풀림).
JWT_SECRET = os.environ.get("JWT_SECRET") or secrets.token_urlsafe(48)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.environ.get("ACCESS_TOKEN_MINUTES", "60"))

# 위험 단계 경계값 임시값 (모델 확정 후 risk_thresholds 테이블·관리자 설정으로 옮김, 03 대조 결과 2)
DEFAULT_THRESHOLDS = {"warning_from": 0.15, "high_from": 0.35}
GRADE_LABELS = {"LOW": "양호", "WARNING": "관리 권장", "HIGH": "상담 권장"}  # 문구 확정 필요 (NFR-014)
DISCLAIMER = "의학적 진단이 아니며 정확한 판단은 의료진과 상담하세요."
