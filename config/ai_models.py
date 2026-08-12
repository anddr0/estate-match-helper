from pydantic import BaseModel, ConfigDict, Field


class AIModelLimits(BaseModel):
    """Locally enforced Gemini API limits for one model."""

    model_config = ConfigDict(frozen=True)

    model_id: str
    requests_per_minute: int = Field(gt=0)
    input_tokens_per_minute: int = Field(gt=0)
    requests_per_day: int = Field(gt=0)


AI_MODEL_LIMITS: tuple[AIModelLimits, ...] = (
    AIModelLimits(
        model_id="gemini-3.5-flash-lite",
        requests_per_minute=15,
        input_tokens_per_minute=250_000,
        requests_per_day=500,
    ),
    AIModelLimits(
        model_id="gemini-3.1-flash-lite",
        requests_per_minute=15,
        input_tokens_per_minute=250_000,
        requests_per_day=500,
    ),
    AIModelLimits(
        model_id="gemma-4-31b-it",
        requests_per_minute=30,
        input_tokens_per_minute=16_000,
        requests_per_day=14_400,
    ),
)

DEFAULT_AI_MODEL = AI_MODEL_LIMITS[0].model_id
