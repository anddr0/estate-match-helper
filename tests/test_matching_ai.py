import unittest
from unittest.mock import AsyncMock, patch

from schemas.property import PropertyData
from services.matching_ai import (
    AI_COMPARISON_RESPONSE_FORMAT,
    clean_json_response,
    evaluate_with_ai,
)


class AIComparisonTests(unittest.IsolatedAsyncioTestCase):
    async def test_validated_ai_score_is_returned(self):
        ai_client = AsyncMock()
        ai_client.generate_text.return_value = '{"score": 0.75, "reason": "partial"}'

        with patch("services.matching_ai.AIClient", return_value=ai_client):
            score = await evaluate_with_ai(
                PropertyData(description="Kitchen connected to living room"),
                "kitchen type",
                "Separate",
                "Check whether the kitchen is separate.",
            )

        self.assertEqual(score, 0.75)
        prompt = ai_client.generate_text.await_args.args[0]
        self.assertIn("kitchen type", prompt)
        self.assertIn("Property offer", prompt)
        self.assertEqual(
            ai_client.generate_text.await_args.kwargs["response_format"],
            AI_COMPARISON_RESPONSE_FORMAT,
        )

    async def test_markdown_json_fence_is_removed_before_validation(self):
        ai_client = AsyncMock()
        ai_client.generate_text.return_value = (
            "```json\n"
            '{"score": 0.5, "reason": "No evidence in the offer."}\n'
            "```"
        )

        with patch("services.matching_ai.AIClient", return_value=ai_client):
            score = await evaluate_with_ai(
                PropertyData(),
                "kitchen type",
                "Separate",
                "Check whether the kitchen is separate.",
            )

        self.assertEqual(score, 0.5)

    def test_clean_json_response_preserves_plain_json(self):
        answer = '  {"score": 1, "reason": "match"}  '

        self.assertEqual(
            clean_json_response(answer),
            '{"score": 1, "reason": "match"}',
        )

    async def test_invalid_ai_response_is_not_used_as_a_score(self):
        ai_client = AsyncMock()
        ai_client.generate_text.return_value = "not json"

        with patch("services.matching_ai.AIClient", return_value=ai_client):
            score = await evaluate_with_ai(
                PropertyData(),
                "design style",
                "minimalist",
                "Check the design.",
            )

        self.assertIsNone(score)


if __name__ == "__main__":
    unittest.main()
