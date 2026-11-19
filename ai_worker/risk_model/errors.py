"""예측 입력 오류."""


class RiskInputError(ValueError):
    """input_snapshot이 입력 계약(feature_spec.yaml)에 맞지 않을 때 발생해요.

    백엔드는 이 오류를 400으로 바꿔 응답하면 됩니다.
    errors: {필드명: 이유} 형식
    """

    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__("입력값 오류: " + ", ".join(f"{k}({v})" for k, v in errors.items()))
