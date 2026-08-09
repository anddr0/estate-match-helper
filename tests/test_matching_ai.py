import unittest
from unittest.mock import AsyncMock, patch

from schemas.property import PropertyData
from services.matching_ai import evaluate_with_ai


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
