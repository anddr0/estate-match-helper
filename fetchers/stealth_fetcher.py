import random
import time

from curl_cffi import requests


class StealthFetcher:
    def __init__(self, impersonate_browser="chrome120"):
        self.session = requests.Session(impersonate=impersonate_browser)

        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        })

    def fetch_page(self, url, min_delay=3.0, max_delay=8.0):
        sleep_time = random.uniform(min_delay, max_delay)
        print(f"[~] Маскируемся. Ждем {sleep_time:.2f} сек. перед запросом...")
        time.sleep(sleep_time)

        try:
            print(f"[>>] Стучимся на: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            return response.text

        except Exception as e:
            print(f"[!] Ошибка при загрузке {url}: {e}")
            return None