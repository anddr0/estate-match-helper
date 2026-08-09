import json

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils.chat_action import ChatActionSender
from loguru import logger
from pydantic import ValidationError

from schemas.client_requirements import ClientRentalRequirements
from services.offers import evaluate_offers, extract_offer_links
from services.requirements import parse_client_requirements
from tg_bot.downloads import download_html
from tg_bot.keyboards import get_confirm_kb, get_stop_kb, get_webapp_keyboard
from tg_bot.states import ParseFlow

router = Router()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
	logger.info(f"Пользователь {message.from_user.id} отменил действие (/cancel).")
	await state.clear()
	await message.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())


@router.message(Command("parse"))
async def cmd_parse(message: Message, state: FSMContext):
	logger.info(f"Пользователь {message.from_user.id} запустил команду /parse.")
	await message.answer("Ожидаю файл HTML. Скинь его мне.")
	await state.set_state(ParseFlow.waiting_for_html)


@router.message(ParseFlow.waiting_for_html, F.document)
async def process_document(message: Message, state: FSMContext, bot: Bot):
	if not message.document.file_name.endswith(".html"):
		logger.warning(f"Пользователь {message.from_user.id} отправил неверный формат файла: {message.document.file_name}")
		await message.answer("Это не HTML файл! 😡\nЖду именно .html (или жми /cancel для отмены).")
		return

	logger.info(f"Получен HTML файл от {message.from_user.id}, начинаем парсинг ссылок...")
	try:
		html_content = await download_html(bot, message.document.file_id)
		links = extract_offer_links(html_content)
	except (OSError, UnicodeDecodeError, ValueError) as e:
		logger.error(f"Ошибка чтения HTML от пользователя {message.from_user.id}: {e}")
		await message.answer("Не удалось прочитать HTML файл.")
		return

	if not links:
		logger.warning(f"В файле пользователя {message.from_user.id} не найдено ссылок.")
		await state.clear()
		await message.answer("В твоем .html файле не найдено ни одной ссылки с обьявлениями( Завершаю процес...")
		return

	logger.success(f"Успешно спаршено {len(links)} ссылок для пользователя {message.from_user.id}.")
	await state.update_data(estate_offers_links=links)

	await message.answer(
		f"🎉 Успешно спаршено! Найдено {len(links)} ссылок.\nТеперь отправь текстовое описание для анализа."
	)
	await state.set_state(ParseFlow.waiting_for_description)


@router.message(ParseFlow.waiting_for_html)
async def process_document_invalid(message: Message):
	await message.answer("Я жду файл документом! 📎\nПришли .html файл или нажми /cancel.")


@router.message(ParseFlow.waiting_for_description, F.text)
async def process_description(message: Message, state: FSMContext, bot: Bot):
	logger.info(f"Получено текстовое описание от {message.from_user.id}, отправляем в нейросеть.")
	await state.update_data(description=message.text)

	await message.answer("Обрабатываем описание...")

	async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
		descr_json = await parse_client_requirements(message.text)

	await state.update_data(descr_json=descr_json)

	await message.answer(
		"Анализ завершен!\n\n"
		"Теперь открой форму ниже, чтобы проверить строгость условий и комментарии:",
		reply_markup=await get_webapp_keyboard(message.from_user.id, descr_json)
	)

	await state.set_state(ParseFlow.waiting_for_web_app)


@router.message(ParseFlow.waiting_for_web_app, F.web_app_data)
async def process_web_app_data(message: Message, state: FSMContext):
	raw_data = message.web_app_data.data
	logger.info(f"Получены данные из WebApp от пользователя {message.from_user.id}.")
	try:
		data = json.loads(raw_data)
	except json.JSONDecodeError as e:
		logger.error(f"Ошибка JSONDecodeError при чтении данных из WebApp от {message.from_user.id}: {e}")
		await message.answer("Ошибка при чтении данных из формы.")
		return

	schema_data_raw = data.get("schema_data", {})
	preferences_text = data.get("client_preferences_text", "")

	try:
		validated_schema = ClientRentalRequirements(**schema_data_raw)
	except ValidationError as e:
		logger.error(f"Ошибка валидации Pydantic модели из WebApp от {message.from_user.id}: {e}")
		await message.answer("Ошибка валидации данных. Пожалуйста, попробуй еще раз.")
		return

	await state.update_data(
		descr_json=validated_schema,
		preferences_text=preferences_text
	)

	await message.answer(
		"Окей, все получил! ✅\n\n"
		"Начинаем обработку ссылок?",
		reply_markup=get_confirm_kb()
	)

	await state.set_state(ParseFlow.waiting_for_confirm)


@router.message(ParseFlow.waiting_for_web_app)
async def process_web_app_invalid(message: Message):
	await message.answer("Пожалуйста, воспользуйся кнопкой, чтобы открыть форму и отправить параметры.")


@router.message(ParseFlow.waiting_for_confirm, F.text.in_({"Да", "Нет"}))
async def process_confirm(message: Message, state: FSMContext):
	if message.text == "Нет":
		logger.info(f"Пользователь {message.from_user.id} отменил обработку ссылок.")
		await state.clear()
		await message.answer("Понял, отменяем.", reply_markup=ReplyKeyboardRemove())
		return

	logger.info(f"Пользователь {message.from_user.id} подтвердил начало обработки ссылок.")
	await state.set_state(ParseFlow.processing)
	await state.update_data(stop_processing=False)
	await message.answer("Начинаю обработку...", reply_markup=get_stop_kb())

	data = await state.get_data()
	links = data.get("estate_offers_links", [])

	if not links:
		logger.error(f"У пользователя {message.from_user.id} отсутствуют ссылки перед стартом обработки.")
		await message.answer("Ошибка: ссылок для обработки не обнаружено", reply_markup=ReplyKeyboardRemove())
		await state.clear()
		return

	client_requirements_raw = data.get("descr_json")
	try:
		client_requirements = ClientRentalRequirements.model_validate(client_requirements_raw)
	except ValidationError as e:
		logger.error(f"Не удалось получить требования клиента перед обработкой: {e}")
		await message.answer("Ошибка: требования клиента отсутствуют или повреждены")
		await state.clear()
		return

	results = await evaluate_offers(links, client_requirements)

	# Проверяем, не нажал ли юзер кнопку "Стоп" пока шла обработка
	current_data = await state.get_data()
	if current_data.get("stop_processing"):
		logger.warning(f"Обработка для {message.from_user.id} была остановлена пользователем.")
		await message.answer("Обработка была остановлена пользователем.", reply_markup=ReplyKeyboardRemove())
		await state.clear()
		return

	# Формируем итоговый ответ
	logger.success(f"Обработка ссылок для {message.from_user.id} успешно завершена.")
	response_lines = ["✅ **Результаты обработки:**\n"]
	for result in results:
		if result.error:
			response_lines.append(f"⚠️ {result.url} -> {result.error}")
			continue
		status_icon = "🟢" if result.factual_score and result.factual_score >= 0.5 else "🔴"
		response_lines.append(
			f"{status_icon} {result.url} -> "
			f"оценка {result.factual_score:.2f}, "
			f"без строгого отсечения {result.potential_score:.2f}"
		)

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
	logger.info(f"Пользователь {message.from_user.id} нажал кнопку 'Стоп'.")
	await state.update_data(stop_processing=True)
	await message.answer("Останавливаю процесс...", reply_markup=ReplyKeyboardRemove())


@router.message(ParseFlow.processing)
async def ignore_during_processing(message: Message):
	pass
