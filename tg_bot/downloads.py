import io

from aiogram import Bot


async def download_html(bot: Bot, file_id: str) -> str:
    buffer = io.BytesIO()
    await bot.download(file=file_id, destination=buffer)
    return buffer.getvalue().decode("utf-8")
