import os
from collections.abc import Iterable

from dotenv import load_dotenv
from loguru import logger
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam

load_dotenv()


class AIClient:
	_instance = None

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
			cls._instance._init_client()
		return cls._instance

	def _init_client(self):
		logger.debug("Инициализация клиента AIClient (OpenRouter/Gemini)")
		api_key = os.getenv("AI_API_KEY")
		if not api_key:
			logger.error("Переменная AI_API_KEY не найдена в окружении (.env)")
			raise ValueError("Переменная AI_API_KEY не найдена в .env")

		self._client = AsyncOpenAI(
			base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
			api_key=api_key,
		)
		logger.debug("Клиент AsyncOpenAI успешно настроен")

	@classmethod
	def get_client(cls) -> AsyncOpenAI:
		return cls()._client

	async def generate_text(self, prompt: str, model: str = "openrouter/free") -> str | None:
		logger.info(f"Генерация текста через модель '{model}' (длина промпта: {len(prompt)} символов)")
		try:
			messages: list[ChatCompletionMessageParam] = [
				ChatCompletionUserMessageParam(role="user", content=prompt)
			]

			response = await self._client.chat.completions.create(
				model=model,
				messages=messages
			)

			answer = response.choices[0].message.content
			logger.info(f"Успешно получен ответ от модели '{model}' (длина ответа: {len(answer) if answer else 0} символов)")
			return answer

		except Exception as e:
			logger.exception(f"Ошибка API OpenRouter при генерации текста с моделью {model}: {e}")
			return None

	async def chat_completion(self, messages: Iterable[ChatCompletionMessageParam],
	                          model: str = "openrouter/free") -> str | None:
		logger.info(f"Запрос chat_completion через модель '{model}'")
		try:
			response = await self._client.chat.completions.create(
				model=model,
				messages=messages
			)

			answer = response.choices[0].message.content
			logger.info(f"Успешный ответ chat_completion от модели '{model}'")
			return answer

		except Exception as e:
			logger.exception(f"Ошибка API OpenRouter в chat_completion с моделью {model}: {e}")
			return None