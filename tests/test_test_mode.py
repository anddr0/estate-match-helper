import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from services.offers import LinkEvaluation
from tg_bot.handlers import process_confirm, process_offer_limit
from tg_bot.states import ParseFlow


class TestModeTests(unittest.IsolatedAsyncioTestCase):
	async def test_offer_limit_must_be_within_parsed_links_count(self):
		message = SimpleNamespace(
			text="4",
			from_user=SimpleNamespace(id=123),
			answer=AsyncMock(),
		)
		state = SimpleNamespace(
			get_data=AsyncMock(return_value={"estate_offers_links": ["one", "two", "three"]}),
			update_data=AsyncMock(),
			set_state=AsyncMock(),
		)

		await process_offer_limit(message, state)

		state.update_data.assert_not_awaited()
		state.set_state.assert_not_awaited()
		message.answer.assert_awaited_once_with("Введи целое число от 1 до 3.")

	async def test_valid_offer_limit_is_saved(self):
		message = SimpleNamespace(
			text="2",
			from_user=SimpleNamespace(id=123),
			answer=AsyncMock(),
		)
		state = SimpleNamespace(
			get_data=AsyncMock(return_value={"estate_offers_links": ["one", "two", "three"]}),
			update_data=AsyncMock(),
			set_state=AsyncMock(),
		)

		await process_offer_limit(message, state)

		state.update_data.assert_awaited_once_with(successful_offer_limit=2)
		state.set_state.assert_awaited_once_with(ParseFlow.waiting_for_description)
		message.answer.assert_awaited_once_with("Теперь отправь текстовое описание для анализа.")

	async def test_processing_counts_only_successful_offers_until_limit(self):
		message = SimpleNamespace(
			text="Да",
			from_user=SimpleNamespace(id=123),
			answer=AsyncMock(),
		)
		state_data = {
			"estate_offers_links": ["broken", "first", "second", "unused"],
			"successful_offer_limit": 2,
			"descr_json": {},
			"stop_processing": False,
		}
		state = SimpleNamespace(
			set_state=AsyncMock(),
			update_data=AsyncMock(),
			get_data=AsyncMock(return_value=state_data),
			clear=AsyncMock(),
		)

		async def fake_results(*args, **kwargs):
			del args, kwargs
			yield LinkEvaluation(url="broken", error="boom")
			yield LinkEvaluation(url="first", factual_score=0.8, potential_score=0.9)
			yield LinkEvaluation(url="second", factual_score=0.7, potential_score=0.8)
			yield LinkEvaluation(url="unused", factual_score=0.9, potential_score=0.9)

		with (
			patch("tg_bot.handlers.ClientRentalRequirements.model_validate", return_value=object()),
			patch("tg_bot.handlers.iter_evaluated_offers", side_effect=fake_results),
		):
			await process_confirm(message, state)

		result_messages = [
			call.args[0]
			for call in message.answer.await_args_list
			if call.kwargs.get("parse_mode") is not None
		]
		self.assertEqual(len(result_messages), 2)
		self.assertNotIn("broken", "".join(result_messages))
		self.assertNotIn("unused", "".join(result_messages))
		self.assertIn("Обработано 1 из 2", result_messages[0])
		self.assertIn("Обработано 2 из 2", result_messages[1])
		self.assertIn("✅ Обработка завершена: 2 из 2", message.answer.await_args_list[-1].args[0])
		state.clear.assert_awaited_once_with()


if __name__ == "__main__":
	unittest.main()
