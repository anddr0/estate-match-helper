import ssl
import uuid

import aiohttp
import certifi
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from loguru import logger

from schemas.client_requirements import ClientRentalRequirements


def get_confirm_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да"), KeyboardButton(text="Нет")]
        ],
        resize_keyboard=True
    )

def get_stop_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🛑 Стоп")]],
        resize_keyboard=True
    )

async def get_webapp_keyboard(user_id: int, schema_data: ClientRentalRequirements) -> ReplyKeyboardMarkup:
    config = {
        "user_id": user_id,
        "schema_data": schema_data.model_dump(mode='json')
    }

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    form_id = None
    try:
        async with aiohttp.ClientSession() as session:  # noqa: SIM117
            async with session.post(
                    url="https://sads-match-helper-forms.pages.dev/api/form",
                    json=config,
                    ssl=ssl_context
            ) as resp:

                if resp.status in (200, 201):
                    data = await resp.json()
                    form_id = data.get("id")
                else:
                    logger.error(f"Failed to create form, status: {resp.status}")
    except (aiohttp.ClientError, OSError) as e:
        logger.error(f"Error creating form: {e}")
    
    if not form_id:
        form_id = str(uuid.uuid4())
    
    web_app_url = f"https://sads-match-helper-forms.pages.dev/?id={form_id}"

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📋 Проверить параметры",
                    web_app=WebAppInfo(url=web_app_url)
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
