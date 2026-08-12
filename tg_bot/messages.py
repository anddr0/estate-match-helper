from html import escape

from services.offers import LinkEvaluation

COMMANDS_HELP_TEXT = (
	"Доступные команды:\n\n"
	"/start — начать работу с ботом и увидеть приветствие.\n"
	"/help — посмотреть список команд и их описание.\n"
	"/parse — запустить обработку HTML-файла с объявлениями.\n"
	"/cancel — отменить текущее действие."
)

START_TEXT = (
	"Привет! 👋 Я помогу проанализировать объявления об аренде и подобрать "
	"варианты под требования клиента.\n\n"
	"Бот находится в разработке. Анализ обьявлений может быть и будет ошибочный или неточный на данном этапе.\n\n"
	"Анализ обьявлений пока возможен только с olx.pl и otodom.pl\n\n"
	f"{COMMANDS_HELP_TEXT}\n\n"
	"Чтобы начать, отправь команду /parse."
)

COMMANDS_PARSE_TEXT = (
	"Чтобы начать анализ обьявлений отправьте HTML файл с обьявлениями с sads.pl\n\n"
	"Инструкция:\n"
	"1. Находясь на странице с обьявлениями sads.pl нажмите на пустом месте ПКМ\n"
	"2. Выберите 'Сохранить страницу как..'\n"
	"3. Выберете место куда сохранить файл и сохраните его\n"
	"4. После сохранения - отправьте его в этот чат\n"
)

PARSE_IN_PROCESS_TEXT = (
	"Обрабатываем описание...\n\n"
	"Сначала отсекаем обьявления, что невозможно обработать, позже будут отправляться обработанные\n"
	"Это займет некоторое время 10-20 минут. Вы можете покинуть этот чат"
)


def _format_score(score: float | None) -> str:
	return "—" if score is None else f"{score * 100:.0f}%"


def _offer_status(score: float | None) -> tuple[str, str]:
	if score is not None and score >= 0.75:
		return "🟢", "Хорошее совпадение"
	if score is not None and score >= 0.5:
		return "🟡", "Частичное совпадение"
	return "🔴", "Слабое совпадение"


def format_offer_result(
	result: LinkEvaluation,
	processed: int,
	total: int,
) -> str:
	"""Build a compact Telegram HTML card for one processed offer."""
	url = escape(result.url, quote=True)
	link = f'<a href="{url}">Открыть объявление</a>'

	if result.error:
		return (
			f"⚠️ <b>Не удалось обработать объявление</b>\n"
			f"{link}\n\n"
			f"<i>Обработано {processed} из {total}</i>"
		)

	icon, status = _offer_status(result.factual_score)
	offer = result.offer
	title = escape(offer.title, quote=False) if offer and offer.title else "Объявление"
	lines = [
		f"{icon} <b>{status}</b>",
		f"<b>{title}</b>",
	]

	if offer and offer.location:
		location_parts = [
			part
			for part in (
				offer.location.city,
				offer.location.subregion,
				offer.location.street,
			)
			if part
		]
		if location_parts:
			lines.append(f"📍 {escape(', '.join(location_parts), quote=False)}")

	if offer and offer.price and offer.price.total is not None:
		price = f"{offer.price.total:,.0f}".replace(",", " ")
		currency = escape(offer.price.currency or "PLN", quote=False)
		lines.append(f"💰 {price} {currency}")

	lines.extend(
		(
			"",
			f"📊 <b>Итоговая оценка:</b> {_format_score(result.factual_score)}",
			f"▫️ Без строгих отсечений: {_format_score(result.potential_score)}",
			"",
			f"🔗 {link}",
			f"<i>Обработано {processed} из {total}</i>",
		)
	)
	return "\n".join(lines)
