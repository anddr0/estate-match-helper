import unittest

from schemas.client_requirements import ClientRentalRequirements
from schemas.property import PropertyData
from services.matching import compare_offer


def _requirements(*, strict_budget: bool = False) -> ClientRentalRequirements:
    return ClientRentalRequirements.model_validate(
        {
            "property_requirements": {
                "min_area_sqm": {"value": 40, "is_strict_requirement": False},
                "rooms_count": {"value": 2, "is_strict_requirement": False},
            },
            "location": {},
            "personal_situation": {
                "tenants_profile": {"adults_count": 1},
                "budget": {
                    "max_total_budget_pln": {
                        "value": 4000,
                        "is_strict_requirement": strict_budget,
                    }
                },
            },
        }
    )


class CompareOfferTests(unittest.TestCase):
    def test_matching_structured_fields(self):
        offer = PropertyData(
            price={"total": 3500, "currency": "PLN"},
            parameters={"Powierzchnia": "45 m²", "Liczba pokoi": "2"},
        )
        self.assertEqual(compare_offer(_requirements(), offer), (1.0, 1.0))

    def test_strict_failure_zeroes_only_factual_score(self):
        offer = PropertyData(
            price={"total": 4500, "currency": "PLN"},
            parameters={"Powierzchnia": "45 m²", "Liczba pokoi": "2"},
        )

        factual, potential = compare_offer(_requirements(strict_budget=True), offer)

        self.assertEqual(factual, 0.0)
        self.assertAlmostEqual(potential, 2 / 3)

    def test_ai_score_can_be_blended_into_draft(self):
        self.assertEqual(
            compare_offer(_requirements(), PropertyData(), ai_score=0.7),
            (0.7, 0.7),
        )


if __name__ == "__main__":
    unittest.main()
