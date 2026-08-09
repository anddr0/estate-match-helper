from clients.stealth_fetcher import StealthFetcher
from utils.logger import setup_logging


def main() -> None:
    setup_logging()
    html_content = StealthFetcher().fetch_page("https://www.olx.pl/")
    if not html_content:
        raise RuntimeError("Fetcher returned no content")
    print(f"Fetched {len(html_content)} characters")


if __name__ == "__main__":
    main()
