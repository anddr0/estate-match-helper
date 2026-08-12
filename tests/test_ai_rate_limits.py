import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from clients.ai import AIClient, AIRateLimitManager
from config.ai_models import AIModelLimits


class AIRateLimitManagerTests(unittest.IsolatedAsyncioTestCase):
    async def test_uses_fallback_when_primary_rpm_is_full(self):
        manager = AIRateLimitManager(
            (
                AIModelLimits(
                    model_id="primary",
                    requests_per_minute=1,
                    input_tokens_per_minute=100,
                    requests_per_day=10,
                ),
                AIModelLimits(
                    model_id="fallback",
                    requests_per_minute=1,
                    input_tokens_per_minute=100,
                    requests_per_day=10,
                ),
            )
        )

        self.assertEqual(await manager.acquire(10, "primary"), "primary")
        self.assertEqual(await manager.acquire(10, "primary"), "fallback")

    async def test_uses_fallback_when_primary_tpm_is_full(self):
        manager = AIRateLimitManager(
            (
                AIModelLimits(
                    model_id="primary",
                    requests_per_minute=10,
                    input_tokens_per_minute=10,
                    requests_per_day=10,
                ),
                AIModelLimits(
                    model_id="fallback",
                    requests_per_minute=10,
                    input_tokens_per_minute=100,
                    requests_per_day=10,
                ),
            )
        )

        self.assertEqual(await manager.acquire(10, "primary"), "primary")
        self.assertEqual(await manager.acquire(10, "primary"), "fallback")

    async def test_uses_fallback_when_primary_daily_limit_is_full(self):
        manager = AIRateLimitManager(
            (
                AIModelLimits(
                    model_id="primary",
                    requests_per_minute=10,
                    input_tokens_per_minute=100,
                    requests_per_day=1,
                ),
                AIModelLimits(
                    model_id="fallback",
                    requests_per_minute=10,
                    input_tokens_per_minute=100,
                    requests_per_day=10,
                ),
            )
        )

        self.assertEqual(await manager.acquire(10, "primary"), "primary")
        self.assertEqual(await manager.acquire(10, "primary"), "fallback")

    async def test_rejects_prompt_larger_than_every_model_tpm(self):
        manager = AIRateLimitManager(
            (
                AIModelLimits(
                    model_id="primary",
                    requests_per_minute=1,
                    input_tokens_per_minute=10,
                    requests_per_day=1,
                ),
            )
        )

        with self.assertRaisesRegex(ValueError, "exceeds every configured model TPM"):
            await manager.acquire(11)

    async def test_server_daily_quota_error_disables_primary_for_the_day(self):
        manager = AIRateLimitManager(
            (
                AIModelLimits(
                    model_id="primary",
                    requests_per_minute=10,
                    input_tokens_per_minute=100,
                    requests_per_day=10,
                ),
                AIModelLimits(
                    model_id="fallback",
                    requests_per_minute=10,
                    input_tokens_per_minute=100,
                    requests_per_day=10,
                ),
            )
        )
        error = MagicMock()
        error.__str__.return_value = "quotaId: GenerateRequestsPerDayPerProject"
        error.response = None

        await manager.report_rate_limit("primary", error)

        self.assertEqual(await manager.acquire(10, "primary"), "fallback")

    def test_production_model_ids_and_limits(self):
        from config.ai_models import AI_MODEL_LIMITS

        self.assertEqual(
            tuple(item.model_id for item in AI_MODEL_LIMITS),
            (
                "gemini-3.5-flash-lite",
                "gemini-3.1-flash-lite",
                "gemma-4-31b-it",
            ),
        )
        self.assertEqual(AI_MODEL_LIMITS[1].requests_per_minute, 15)
        self.assertEqual(AI_MODEL_LIMITS[1].input_tokens_per_minute, 250_000)
        self.assertEqual(AI_MODEL_LIMITS[1].requests_per_day, 500)
        self.assertEqual(AI_MODEL_LIMITS[2].requests_per_day, 14_400)


class AIClientResponseFormatTests(unittest.IsolatedAsyncioTestCase):
    async def test_response_format_is_forwarded_to_api_request(self):
        client = object.__new__(AIClient)
        create = AsyncMock(
            return_value=SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))]
            )
        )
        client._client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
        client._rate_limits = SimpleNamespace(
            acquire=AsyncMock(return_value="primary"),
            model_ids=("primary",),
        )
        response_format = {"type": "json_object"}

        answer = await client.generate_text(
            "Return JSON",
            model="primary",
            response_format=response_format,
        )

        self.assertEqual(answer, '{"ok": true}')
        self.assertEqual(create.await_args.kwargs["response_format"], response_format)


if __name__ == "__main__":
    unittest.main()
