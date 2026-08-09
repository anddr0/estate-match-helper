import json
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from clients.ai import AIClient
from config.settings import GEMINI_FLASH_LITE_MODEL
from schemas.property import PropertyData


class AIComparisonResponse(BaseModel):
    score: float = Field(ge=0, le=1)
    reason: str


BASE_MATCHING_PROMPT = """
You evaluate one specific rental requirement against one property offer.
Use only facts present in the supplied property JSON. Do not invent facts.
Return only JSON: {"score": <number from 0 to 1>, "reason": "<short reason>"}.
A score of 1 means the requirement is fully satisfied, 0 means it clearly fails.
If evidence is missing, use 0.5 to represent uncertainty.
""".strip()


async def evaluate_with_ai(
    offer: PropertyData,
    requirement_name: str,
    requirement_value: Any,
    additional_instructions: str,
) -> float | None:
    """Universal AI fallback shared by all semantic matching evaluators."""
    prompt = f"""
{BASE_MATCHING_PROMPT}

Requirement name: {requirement_name}
Requirement value:
{json.dumps(requirement_value, ensure_ascii=False)}

Additional evaluation instructions:
{additional_instructions}

Property offer:
{offer.model_dump_json(exclude_none=True)}
""".strip()

    answer = await AIClient().generate_text(prompt, model=GEMINI_FLASH_LITE_MODEL)
    if not answer:
        logger.warning(f"AI returned no score for requirement {requirement_name}")
        return None

    try:
        return AIComparisonResponse.model_validate_json(answer).score
    except ValidationError as exc:
        logger.error(f"Invalid AI matching response for {requirement_name}: {exc}")
        return None
