from collections.abc import Mapping
from typing import Protocol
from urllib.parse import urlparse

from parsers.base import BaseParser
from parsers.olx import OlxParser
from parsers.otodom import OtodomParser
from schemas.property import ParsedPropertyResponse


class PageFetcher(Protocol):
    def fetch_page(self, url: str) -> str | None: ...


class UnsupportedPropertySiteError(ValueError):
    """No property parser is registered for the URL host."""


class PropertyFetchError(RuntimeError):
    """The offer page could not be downloaded."""


class PropertyParseError(RuntimeError):
    """A known parser could not extract an offer from the page."""


PARSERS: Mapping[str, type[BaseParser]] = {
    "olx.pl": OlxParser,
    "otodom.pl": OtodomParser,
}


def parser_for_url(url: str) -> type[BaseParser]:
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
        raise ValueError(f"Некорректный URL оферты: {url!r}")

    hostname = parsed_url.hostname.lower().rstrip(".")
    for registered_host, parser_class in PARSERS.items():
        if hostname == registered_host or hostname.endswith(f".{registered_host}"):
            return parser_class

    raise UnsupportedPropertySiteError(
        f"Для сайта {hostname!r} пока нет зарегистрированного парсера"
    )


def parse_property_url(
    url: str,
    fetcher: PageFetcher | None = None,
) -> ParsedPropertyResponse:
    """Download an offer and route its HTML to the parser for that domain."""
    parser_class = parser_for_url(url)
    if fetcher is None:
        from clients.stealth_fetcher import StealthFetcher

        fetcher = StealthFetcher()

    html_content = fetcher.fetch_page(url)
    if not html_content:
        raise PropertyFetchError(f"Не удалось загрузить страницу: {url}")

    result = parser_class(html_content).parse()
    if not isinstance(result, ParsedPropertyResponse):
        result = ParsedPropertyResponse.model_validate(result)
    if result.status != "success" or result.data is None:
        raise PropertyParseError(result.error or f"Не удалось распарсить оферту: {url}")

    if result.data.url is None:
        result.data.url = url
    return result
