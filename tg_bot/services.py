import io
import asyncio
import random
from aiogram import Bot

from clients.open_router import AIClient
from parsers.sads import SadsParser
from utils.constans.models import GEMINI_3_5_FLASH_LITE
from utils.utils import get_client_requirements_prompt


async def process_estate_description(description: str) -> str | None:
    or_client = AIClient()
    prompt = get_client_requirements_prompt(description)

    answer = await or_client.generate_text(
        prompt=prompt,
        model=GEMINI_3_5_FLASH_LITE
    )

    return answer

async def mock_parse_html(bot: Bot, file_id: str) -> list[str]:
    file_buffer = io.BytesIO()
    await bot.download(file=file_id, destination=file_buffer)
    file_buffer.seek(0)

    html_content = file_buffer.read().decode('utf-8')
    try:
        parser = SadsParser(html_content)
        links = parser.parse()
        return links
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        return []

async def mock_evaluate_link(link: str, description: str) -> tuple[bool, str]:
    await asyncio.sleep(random.uniform(0.5, 2.0))

    # Моковая логика успешности (например, 50/50)
    is_match = random.choice([True, False])
    result_text = f"Проанализировано с описанием: '{description[:15]}...'"

    return is_match, f"{link} -> {result_text}"

async def process_links_concurrently(links: list[str], description: str) -> list[tuple[bool, str]]:
    tasks = [mock_evaluate_link(link, description) for link in links]
    return await asyncio.gather(*tasks)