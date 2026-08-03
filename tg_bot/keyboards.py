import json
import urllib.parse
import uuid

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from schemas.client_requirements_model import ClientRentalRequirements


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

def get_webapp_keyboard(user_id: int, schema_data: ClientRentalRequirements) -> ReplyKeyboardMarkup:
    config = {
        "user_id": user_id,
        "session_uuid": str(uuid.uuid4()),
        "schema_data": schema_data.model_dump_json()
    }
    json_str = json.dumps(config, ensure_ascii=False)
    encoded_data = urllib.parse.quote(json_str)

    base_url = "https://anddr0.github.io/sads-estate-match-helper-forms/"
    web_app_url = f"{base_url}?data={encoded_data}"

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