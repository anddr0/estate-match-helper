from loguru import logger

from clients.stealth_fetcher import StealthFetcher


def test_fetcher():
	logger.info("Запуск тестового скрипта для проверки StealthFetcher...")

	test_url = "https://www.olx.pl/"

	fetcher = StealthFetcher(impersonate_browser="chrome120")
	html_content = fetcher.fetch_page(test_url)

	if html_content:
		logger.info(f"Тест успешно пройден! Получено HTML размером {len(html_content)} символов.")
	else:
		logger.warning("Тест завершился без контента (возможно, сработала защита или нет сети).")

if __name__ == "__main__":
	test_fetcher()