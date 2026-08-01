import json
from pathlib import Path

def get_client_requirements_prompt(description: str, schema_path: str = "schemas/client_requirements_schema.json") -> str:
    path = Path(schema_path)
    with open(path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    prompt = f"""
You are an expert real estate assistant. Your task is to extract tenant requirements from the given text and map them into a JSON object adhering STRICTLY to the provided JSON Schema.

### INSTRUCTIONS:
1. Extract all requirements in detail (property parameters, location, tenant profile, budget, etc.).
2. For fields that contain an `is_strict_requirement` property:
   - Set `is_strict_requirement: true` ONLY if the tenant explicitly indicates a strict/mandatory constraint (e.g., "strictly 2 rooms", "no ground floor", "must have balcony", "max budget 4000").
   - Set `is_strict_requirement: false` if it is a preference, flexible request, or default choice (e.g., "would be nice to have a balcony", "preferably close to center"). Default is false.
3. If information for a non-required field is missing in the description, you must always set its value to null. Omitting or removing the property from the payload/schema is strictly prohibited.
4. Output MUST be a valid JSON object matching the schema below. Do NOT wrap in markdown blocks if using direct structured outputs, or output purely valid JSON with no conversational text.

### JSON SCHEMA:
{json.dumps(schema, ensure_ascii=False, indent=2)}

### INPUT DESCRIPTION:
{description}
"""
    return prompt.strip()