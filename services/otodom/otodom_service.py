from clients.stealth_fetcher import StealthFetcher
from parsers.otodom import OtodomParser


def process_otodom_url(url: str) -> dict:
    fetcher = StealthFetcher()
    html_content = fetcher.fetch_page(url)

    if not html_content:
        raise Exception("Не удалось загрузить страницу. Возможно, сработала капча.")

    parser = OtodomParser(html_content)
    data = parser.parse()

    return data