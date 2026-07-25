from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from tg_bot.keyboards import get_confirm_kb, get_stop_kb
from tg_bot.services import process_links_concurrently, mock_parse_html
from tg_bot.states import ParseFlow

router = Router()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
	await state.clear()
	await message.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())


@router.message(Command("parse"))
async def cmd_parse(message: Message, state: FSMContext):
	await message.answer("Ожидаю файл HTML. Скинь его мне.")
	await state.set_state(ParseFlow.waiting_for_html)


@router.message(ParseFlow.waiting_for_html, F.document)
async def process_document(message: Message, state: FSMContext, bot: Bot):
	if not message.document.file_name.endswith(".html"):
		await message.answer("Это не HTML файл! 😡\nЖду именно .html (или жми /cancel для отмены).")
		return

	links = await mock_parse_html(bot, message.document.file_id)
	await state.update_data(otodom_links=links)

	await message.answer(
		f"🎉 Успешно спаршено! Найдено {len(links)} ссылок.\nТеперь отправь текстовое описание для анализа."
	)
	await state.set_state(ParseFlow.waiting_for_description)


@router.message(ParseFlow.waiting_for_html)
async def process_document_invalid(message: Message):
	await message.answer("Я жду файл документом! 📎\nПришли .html файл или нажми /cancel.")


@router.message(ParseFlow.waiting_for_description, F.text)
async def process_description(message: Message, state: FSMContext):
	await state.update_data(description=message.text)

	await message.answer(
		"Описание принято! Желаете начать обработку?",
		reply_markup=get_confirm_kb()
	)
	await state.set_state(ParseFlow.waiting_for_confirm)


@router.message(ParseFlow.waiting_for_confirm, F.text.in_({"Да", "Нет"}))
async def process_confirm(message: Message, state: FSMContext):
	if message.text == "Нет":
		await state.clear()
		await message.answer("Понял, отменяем.", reply_markup=ReplyKeyboardRemove())
		return

	await state.set_state(ParseFlow.processing)
	await state.update_data(stop_processing=False)
	await message.answer("Начинаю параллельную обработку...", reply_markup=get_stop_kb())

	data = await state.get_data()
	links = data.get("otodom_links", [])
	description = data.get("description", "")

	# Запускаем параллельную обработку
	results = await process_links_concurrently(links, description)

	# Проверяем, не нажал ли юзер кнопку "Стоп" пока шла обработка
	current_data = await state.get_data()
	if current_data.get("stop_processing"):
		await message.answer("Обработка была остановлена пользователем.", reply_markup=ReplyKeyboardRemove())
		await state.clear()
		return

	# Формируем итоговый ответ
	response_lines = ["✅ **Результаты обработки:**\n"]
	for is_match, text_result in results:
		status_icon = "🟢" if is_match else "🔴"
		response_lines.append(f"{status_icon} {text_result}")

	final_text = "\n".join(response_lines)

	# Отправляем чанками, если текст превышает лимит Telegram (4096)
	max_length = 4000
	for i in range(0, len(final_text), max_length):
		await message.answer(final_text[i: i + max_length])

	await message.answer("Обработка полностью завершена!", reply_markup=ReplyKeyboardRemove())
	await state.clear()


@router.message(ParseFlow.waiting_for_confirm)
async def process_confirm_invalid(message: Message):
	await message.answer("Используй кнопки 'Да' или 'Нет' внизу экрана.")


@router.message(ParseFlow.processing, F.text == "🛑 Стоп")
async def stop_processing(message: Message, state: FSMContext):
	# Обновляем флаг. Результат gather() просто будет проигнорирован в конце.
	await state.update_data(stop_processing=True)
	await message.answer("Останавливаю процесс...", reply_markup=ReplyKeyboardRemove())


@router.message(ParseFlow.processing)
async def ignore_during_processing(message: Message):
	pass