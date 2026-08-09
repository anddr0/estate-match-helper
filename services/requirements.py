import json
from pathlib import Path

from clients.ai import AIClient
from config.settings import GEMINI_FLASH_LITE_MODEL
from schemas.client_requirements import ClientRentalRequirements

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "client_requirements_schema.json"


def build_requirements_prompt(description: str) -> str:
    with SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        schema = json.load(schema_file)

    return f"""
You are an expert real estate assistant. Extract tenant requirements from the
input and return a JSON object that strictly follows the provided JSON Schema.

Rules:
1. Extract property, location, tenant and budget requirements in detail.
2. Set `is_strict_requirement` to true only for an explicitly mandatory limit.
3. Set missing non-required values to null; do not remove schema properties.
4. Return only valid JSON without Markdown or conversational text.

JSON Schema:
{json.dumps(schema, ensure_ascii=False, indent=2)}

Input description:
{description}
""".strip()


async def parse_client_requirements(description: str) -> ClientRentalRequirements:
    answer = await AIClient().generate_text(
        prompt=build_requirements_prompt(description),
        model=GEMINI_FLASH_LITE_MODEL,
    )
    if not answer:
        raise RuntimeError("AI did not return client requirements")
    return ClientRentalRequirements.model_validate_json(answer)
