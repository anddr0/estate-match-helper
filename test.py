from rich.pretty import pprint

from fetchers.stealth_fetcher import StealthFetcher
from parsers.olx import OlxParser

with open("olx_offer.html", "r") as f:
	content = f.read()


parser = OlxParser("olx_offer.html")
parsed_content = parser.parse()

pprint(parsed_content)
