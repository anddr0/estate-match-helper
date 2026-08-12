import asyncio
import json
import math
import os
import time
from collections import defaultdict, deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from loguru import logger
from openai import AsyncOpenAI, OpenAIError, RateLimitError
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam
from openai.types.chat.completion_create_params import ResponseFormat

from config.ai_models import AI_MODEL_LIMITS, DEFAULT_AI_MODEL, AIModelLimits

load_dotenv()

_MINUTE_SECONDS = 60.0
_PACIFIC_TIME = ZoneInfo("America/Los_Angeles")


@dataclass(frozen=True)
class _Usage:
    created_at: float
    input_tokens: int


class AIRateLimitManager:
    """Coordinates concurrent requests and transparently selects a fallback model."""

    def __init__(self, limits: Sequence[AIModelLimits] = AI_MODEL_LIMITS):
        if not limits:
            raise ValueError("At least one AI model must be configured")

        self._limits = tuple(limits)
        self._by_model = {item.model_id: item for item in self._limits}
        if len(self._by_model) != len(self._limits):
            raise ValueError("AI model IDs must be unique")

        self._minute_usage: dict[str, deque[_Usage]] = defaultdict(deque)
        self._daily_usage: dict[tuple[str, str], int] = defaultdict(int)
        self._cooldown_until: dict[str, float] = defaultdict(float)
        self._lock = asyncio.Lock()

    @property
    def model_ids(self) -> tuple[str, ...]:
        return tuple(item.model_id for item in self._limits)

    async def acquire(
        self,
        input_tokens: int,
        preferred_model: str | None = None,
        excluded_models: set[str] | None = None,
    ) -> str:
        """Reserve capacity, waiting only when every usable model is busy."""
        input_tokens = max(input_tokens, 1)
        excluded_models = excluded_models or set()
        ordered_limits = self._ordered_limits(preferred_model)
        usable_limits = [
            limit for limit in ordered_limits if limit.model_id not in excluded_models
        ]
        if not usable_limits:
            raise ValueError("All configured AI models are excluded")
        if all(
            input_tokens > limit.input_tokens_per_minute for limit in usable_limits
        ):
            largest_tpm = max(
                limit.input_tokens_per_minute for limit in usable_limits
            )
            raise ValueError(
                f"Estimated prompt size ({input_tokens} tokens) exceeds every "
                f"configured model TPM limit (largest: {largest_tpm})"
            )

        while True:
            async with self._lock:
                now = time.monotonic()
                today = self._pacific_day()
                wait_times: list[float] = []

                for limit in ordered_limits:
                    model = limit.model_id
                    if model in excluded_models:
                        continue
                    if input_tokens > limit.input_tokens_per_minute:
                        continue

                    usage = self._minute_usage[model]
                    self._prune_minute_usage(usage, now)
                    daily_key = (model, today)
                    if self._daily_usage[daily_key] >= limit.requests_per_day:
                        continue

                    wait_for = max(0.0, self._cooldown_until[model] - now)
                    wait_for = max(
                        wait_for,
                        self._minute_wait(usage, limit, input_tokens, now),
                    )
                    if wait_for > 0:
                        wait_times.append(wait_for)
                        continue

                    usage.append(_Usage(now, input_tokens))
                    self._daily_usage[daily_key] += 1
                    logger.debug(
                        "Зарезервирован AI-запрос: model={}, rpm={}/{}, "
                        "tpm={}/{}, rpd={}/{}",
                        model,
                        len(usage),
                        limit.requests_per_minute,
                        sum(item.input_tokens for item in usage),
                        limit.input_tokens_per_minute,
                        self._daily_usage[daily_key],
                        limit.requests_per_day,
                    )
                    return model

                if wait_times:
                    wait_for = max(0.01, min(wait_times))
                else:
                    wait_for = self._seconds_until_pacific_midnight()

            logger.info("Все AI-модели заняты лимитами; ожидание {:.1f} сек.", wait_for)
            await asyncio.sleep(wait_for)

    async def report_rate_limit(self, model: str, error: RateLimitError) -> None:
        """Apply a server-side 429 to local state before selecting another model."""
        message = str(error).lower()
        retry_after = self._retry_after_seconds(error)

        async with self._lock:
            now = time.monotonic()
            limit = self._by_model.get(model)
            if limit and self._is_daily_quota_error(message):
                self._daily_usage[(model, self._pacific_day())] = limit.requests_per_day
                logger.warning("Исчерпан суточный лимит модели {}", model)
                return

            cooldown = retry_after if retry_after is not None else _MINUTE_SECONDS
            self._cooldown_until[model] = max(
                self._cooldown_until[model],
                now + max(0.01, cooldown),
            )
            logger.warning(
                "Модель {} получила 429; локальная пауза {:.1f} сек.",
                model,
                cooldown,
            )

    def _ordered_limits(self, preferred_model: str | None) -> tuple[AIModelLimits, ...]:
        if preferred_model is None:
            return self._limits
        preferred = self._by_model.get(preferred_model)
        if preferred is None:
            raise ValueError(f"Model {preferred_model!r} has no configured limits")
        return (preferred, *(item for item in self._limits if item != preferred))

    @staticmethod
    def _prune_minute_usage(usage: deque[_Usage], now: float) -> None:
        while usage and now - usage[0].created_at >= _MINUTE_SECONDS:
            usage.popleft()

    @staticmethod
    def _minute_wait(
        usage: deque[_Usage],
        limit: AIModelLimits,
        input_tokens: int,
        now: float,
    ) -> float:
        if len(usage) < limit.requests_per_minute and (
            sum(item.input_tokens for item in usage) + input_tokens
            <= limit.input_tokens_per_minute
        ):
            return 0.0

        remaining_requests = len(usage)
        remaining_tokens = sum(item.input_tokens for item in usage)
        for item in usage:
            remaining_requests -= 1
            remaining_tokens -= item.input_tokens
            if remaining_requests < limit.requests_per_minute and (
                remaining_tokens + input_tokens <= limit.input_tokens_per_minute
            ):
                return max(0.0, item.created_at + _MINUTE_SECONDS - now)
        return _MINUTE_SECONDS

    @staticmethod
    def _pacific_day() -> str:
        return datetime.now(_PACIFIC_TIME).date().isoformat()

    @staticmethod
    def _seconds_until_pacific_midnight() -> float:
        now = datetime.now(_PACIFIC_TIME)
        tomorrow = datetime.combine(
            now.date() + timedelta(days=1),
            datetime.min.time(),
            tzinfo=_PACIFIC_TIME,
        )
        return max(1.0, (tomorrow - now).total_seconds())

    @staticmethod
    def _is_daily_quota_error(message: str) -> bool:
        daily_markers = (
            "per day",
            "per_day",
            "requestsperday",
            "rpd",
            "daily",
        )
        return any(marker in message for marker in daily_markers)

    @staticmethod
    def _retry_after_seconds(error: RateLimitError) -> float | None:
        response = getattr(error, "response", None)
        if response is None:
            return None
        value = response.headers.get("retry-after")
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(value)
                now = datetime.now(retry_at.tzinfo)
                return max(0.0, (retry_at - now).total_seconds())
            except (TypeError, ValueError):
                return None


class AIClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self) -> None:
        logger.debug("Инициализация клиента AIClient (Google Gemini API)")
        api_key = os.getenv("AI_API_KEY")
        if not api_key:
            logger.error("Переменная AI_API_KEY не найдена в окружении (.env)")
            raise ValueError("Переменная AI_API_KEY не найдена в .env")

        self._client = AsyncOpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key,
        )
        self._rate_limits = AIRateLimitManager()
        logger.debug("Клиент AsyncOpenAI успешно настроен")

    @classmethod
    def get_client(cls) -> AsyncOpenAI:
        return cls()._client

    async def generate_text(
        self,
        prompt: str,
        model: str = DEFAULT_AI_MODEL,
        response_format: ResponseFormat | None = None,
    ) -> str | None:
        messages: list[ChatCompletionMessageParam] = [
            ChatCompletionUserMessageParam(role="user", content=prompt)
        ]
        return await self.chat_completion(
            messages,
            model=model,
            response_format=response_format,
        )

    async def chat_completion(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        model: str = DEFAULT_AI_MODEL,
        response_format: ResponseFormat | None = None,
    ) -> str | None:
        message_list = list(messages)
        input_tokens = self._estimate_input_tokens(message_list, response_format)
        failed_models: set[str] = set()

        while True:
            selected_model = await self._rate_limits.acquire(
                input_tokens=input_tokens,
                preferred_model=model,
                excluded_models=failed_models,
            )
            logger.info(
                "Запрос chat_completion через модель '{}' (оценка: {} input tokens)",
                selected_model,
                input_tokens,
            )
            try:
                if response_format is None:
                    response = await self._client.chat.completions.create(
                        model=selected_model,
                        messages=message_list,
                    )
                else:
                    response = await self._client.chat.completions.create(
                        model=selected_model,
                        messages=message_list,
                        response_format=response_format,
                    )
                answer = response.choices[0].message.content
                logger.info("Успешный ответ от модели '{}'", selected_model)
                return answer
            except RateLimitError as exc:
                await self._rate_limits.report_rate_limit(selected_model, exc)
                failed_models.add(selected_model)
                if failed_models == set(self._rate_limits.model_ids):
                    failed_models.clear()
            except OpenAIError as exc:
                logger.exception(
                    "Ошибка Google AI API при запросе к модели {}: {}",
                    selected_model,
                    exc,
                )
                return None

    @staticmethod
    def _estimate_input_tokens(
        messages: Sequence[ChatCompletionMessageParam],
        response_format: ResponseFormat | None = None,
    ) -> int:
        # A conservative local approximation avoids an extra countTokens API call.
        request_input = {
            "messages": messages,
            "response_format": response_format,
        }
        serialized = json.dumps(request_input, ensure_ascii=False, default=str)
        return max(1, math.ceil(len(serialized.encode("utf-8")) / 3))
