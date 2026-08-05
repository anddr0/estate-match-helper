import random
import time

from curl_cffi import requests
from loguru import logger

from utils.constans.constants import (
    MAX_DELAY_BEFORE_URL_FETCH,
    MIN_DELAY_BEFORE_URL_FETCH,
)
from utils.constans.headers import CHROME_SESSION_HEADERS


class StealthFetcher:
    def __init__(self, impersonate_browser="chrome120"):
        logger.debug(f"Инициализация StealthFetcher с профилем браузера: {impersonate_browser}")
        self.session = requests.Session(impersonate=impersonate_browser)

        self.session.headers.update(CHROME_SESSION_HEADERS)
        logger.debug("Заголовки сессии StealthFetcher успешно обновлены")

    def fetch_page(self, url, min_delay=MIN_DELAY_BEFORE_URL_FETCH, max_delay=MAX_DELAY_BEFORE_URL_FETCH):
        sleep_time = random.uniform(min_delay, max_delay)
        logger.info(f"Маскируемся. Ждем {sleep_time:.2f} сек. перед запросом к {url}")
        time.sleep(sleep_time)

        try:
            logger.info(f"Выполняется GET-запрос на URL: {url}")
            response = self.session.get(url, timeout=15)

            logger.debug(f"Получен ответ от {url} со статусом {response.status_code}")
            response.raise_for_status()

            logger.info(f"Страница успешно загружена: {url} (размер контента: {len(response.text)} символов)")
            return response.text

        except requests.errors.RequestsError as e:
            logger.error(f"Сетевая ошибка при запросе к {url}: {e}")
            return None
        except Exception as e:
            logger.exception(f"Непредвиденная ошибка при загрузке страницы {url}: {e}")
            return None