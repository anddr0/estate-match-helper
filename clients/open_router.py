import os
from typing import Iterable
from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam

load_dotenv()


class AIClient:
	_instance = None

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super(AIClient, cls).__new__(cls)
			cls._instance._init_client()
		return cls._instance

	def _init_client(self):
		api_key = os.getenv("AI_API_KEY")
		if not api_key:
			raise ValueError("Переменная AI_API_KEY не найдена в .env")

		self._client = AsyncOpenAI(
			base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
			api_key=api_key,
		)

	@classmethod
	def get_client(cls) -> AsyncOpenAI:
		return cls()._client

	async def generate_text(self, prompt: str, model: str = "openrouter/free") -> str | None:
		try:
			messages: list[ChatCompletionMessageParam] = [
				ChatCompletionUserMessageParam(role="user", content=prompt)
			]

			response = await self._client.chat.completions.create(
				model=model,
				messages=messages
			)

			return response.choices[0].message.content
		except Exception as e:
			print(f"Ошибка API OpenRouter: {e}")
			return None

	async def chat_completion(self, messages: Iterable[ChatCompletionMessageParam],
	                          model: str = "openrouter/free") -> str | None:
		try:
			response = await self._client.chat.completions.create(
				model=model,
				messages=messages
			)

			return response.choices[0].message.content
		except Exception as e:
			print(f"Ошибка API OpenRouter: {e}")
			return None