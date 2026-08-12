import asyncio
import unittest
from unittest.mock import patch

from services.offers import LinkEvaluation, iter_evaluated_offers


class OfferStreamingTests(unittest.IsolatedAsyncioTestCase):
    async def test_yields_offers_in_completion_order(self):
        release_slow_offer = asyncio.Event()

        async def fake_evaluate_offer(url, client_requirements):
            del client_requirements
            if url == "slow":
                await release_slow_offer.wait()
            else:
                release_slow_offer.set()
            return LinkEvaluation(url=url, factual_score=1, potential_score=1)

        with patch("services.offers.evaluate_offer", side_effect=fake_evaluate_offer):
            results = [
                result
                async for result in iter_evaluated_offers(
                    ["slow", "fast"],
                    client_requirements=object(),
                )
            ]

        self.assertEqual([result.url for result in results], ["fast", "slow"])


if __name__ == "__main__":
    unittest.main()
