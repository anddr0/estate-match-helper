import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from tg_bot.handlers import cmd_help, cmd_start
from tg_bot.messages import COMMANDS_HELP_TEXT, START_TEXT


class BotCommandTests(unittest.IsolatedAsyncioTestCase):
	async def test_start_clears_state_and_sends_welcome_with_next_step(self):
		message = SimpleNamespace(
			from_user=SimpleNamespace(id=123),
			answer=AsyncMock(),
		)
		state = SimpleNamespace(clear=AsyncMock())

		await cmd_start(message, state)

		state.clear.assert_awaited_once_with()
		message.answer.assert_awaited_once()
		self.assertEqual(message.answer.await_args.args[0], START_TEXT)
		self.assertIn("/parse", START_TEXT)

	async def test_help_sends_all_command_descriptions(self):
		message = SimpleNamespace(
			from_user=SimpleNamespace(id=123),
			answer=AsyncMock(),
		)

		await cmd_help(message)

		message.answer.assert_awaited_once_with(COMMANDS_HELP_TEXT)
		for command in ("/start", "/help", "/parse", "/cancel"):
			self.assertIn(command, COMMANDS_HELP_TEXT)


if __name__ == "__main__":
	unittest.main()
