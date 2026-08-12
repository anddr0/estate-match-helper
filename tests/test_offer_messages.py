import unittest

from schemas.property import PropertyData
from services.offers import LinkEvaluation
from tg_bot.messages import format_offer_result


class OfferMessageTests(unittest.TestCase):
    def test_formats_successful_offer_as_html_card(self):
        result = LinkEvaluation(
            url="https://example.com/offer?a=1&b=2",
            factual_score=0.82,
            potential_score=0.91,
            offer=PropertyData(
                title="Mieszkanie <centrum>",
                price={"total": 4250, "currency": "PLN"},
                location={"city": "Warszawa", "subregion": "Mokotów"},
            ),
        )

        text = format_offer_result(result, processed=2, total=5)

        self.assertIn("🟢 <b>Хорошее совпадение</b>", text)
        self.assertIn("Mieszkanie &lt;centrum&gt;", text)
        self.assertIn("📍 Warszawa, Mokotów", text)
        self.assertIn("💰 4 250 PLN", text)
        self.assertIn("Итоговая оценка:</b> 82%", text)
        self.assertIn("Без строгих отсечений: 91%", text)
        self.assertIn(
            '<a href="https://example.com/offer?a=1&amp;b=2">Открыть объявление</a>',
            text,
        )
        self.assertNotIn("https://example.com/offer?a=1&b=2", text)
        self.assertIn("Обработано 2 из 5", text)

    def test_formats_failed_offer_without_exposing_internal_error(self):
        result = LinkEvaluation(
            url="https://example.com/broken",
            error="internal stack details",
        )

        text = format_offer_result(result, processed=1, total=1)

        self.assertIn("Не удалось обработать объявление", text)
        self.assertIn("Открыть объявление", text)
        self.assertNotIn("internal stack details", text)


if __name__ == "__main__":
    unittest.main()
