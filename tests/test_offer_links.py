import unittest

from services.offers import extract_offer_links


class OfferLinksTests(unittest.TestCase):
    def test_extracts_only_source_offer_links(self):
        html = """
        <a href="https://www.olx.pl/offer/1">Źródło oferty</a>
        <a href="https://example.com/other">Other</a>
        """

        self.assertEqual(
            extract_offer_links(html),
            ["https://www.olx.pl/offer/1"],
        )


if __name__ == "__main__":
    unittest.main()
