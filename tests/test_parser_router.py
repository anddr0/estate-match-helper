import unittest

from parsers.olx import OlxParser
from parsers.otodom import OtodomParser
from parsers.router import (
    UnsupportedPropertySiteError,
    parse_property_url,
    parser_for_url,
)


class _Fetcher:
    def __init__(self, html: str):
        self.html = html

    def fetch_page(self, url: str) -> str:
        return self.html


class ParserRouterTests(unittest.TestCase):
    def test_selects_parser_for_domain_and_subdomain(self):
        self.assertIs(parser_for_url("https://www.olx.pl/d/oferta/1"), OlxParser)
        self.assertIs(parser_for_url("https://otodom.pl/pl/oferta/1"), OtodomParser)

    def test_rejects_unknown_domain(self):
        with self.assertRaises(UnsupportedPropertySiteError):
            parser_for_url("https://example.com/offer/1")

    def test_returns_common_model_and_preserves_input_url(self):
        html = """
        <script type="application/ld+json">
        {"sku":"1","name":"Flat","description":"Nice","offers":{"price":3000}}
        </script>
        """

        result = parse_property_url("https://www.olx.pl/d/oferta/1", _Fetcher(html))

        self.assertEqual(result.status, "success")
        self.assertEqual(result.data.url, "https://www.olx.pl/d/oferta/1")


if __name__ == "__main__":
    unittest.main()
