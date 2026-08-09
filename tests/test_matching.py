import unittest
from unittest.mock import AsyncMock, patch

from schemas.client_requirements import (
    ClientRentalRequirements,
    FloorPreference,
    Requirement,
)
from schemas.property import PropertyData
from services.matching import (
    compare_offer,
    evaluate_floor_preference,
    evaluate_has_balcony,
    evaluate_max_total_budget,
    evaluate_min_area,
)


def _requirements(*, strict_budget: bool = False, kitchen_type: str | None = None):
    return ClientRentalRequirements.model_validate(
        {
            "property_requirements": {
                "min_area_sqm": {"value": 40, "is_strict_requirement": False},
                "rooms_count": {"value": 2, "is_strict_requirement": False},
                "kitchen_type": (
                    {"value": kitchen_type, "is_strict_requirement": False}
                    if kitchen_type
                    else None
                ),
            },
            "location": {},
            "personal_situation": {
                "tenants_profile": {"adults_count": 1},
                "budget": {
                    "max_total_budget_pln": {
                        "value": 4200,
                        "is_strict_requirement": strict_budget,
                    }
                },
            },
        }
    )


class NumericEvaluatorTests(unittest.TestCase):
    def test_budget_is_one_when_offer_is_below_limit(self):
        requirement = Requirement(value=4200, is_strict_requirement=False)
        offer = PropertyData(price={"total": 3900})

        self.assertEqual(evaluate_max_total_budget(requirement, offer), 1.0)

    def test_budget_degrades_smoothly_for_non_strict_requirement(self):
        requirement = Requirement(value=4200, is_strict_requirement=False)

        close_offer = PropertyData(price={"total": 4300})
        expensive_offer = PropertyData(price={"total": 5300})

        self.assertAlmostEqual(
            evaluate_max_total_budget(requirement, close_offer),
            0.807,
            places=2,
        )
        self.assertAlmostEqual(
            evaluate_max_total_budget(requirement, expensive_offer),
            0.095,
            places=2,
        )

    def test_budget_is_zero_after_strict_limit_is_exceeded(self):
        requirement = Requirement(value=4200, is_strict_requirement=True)

        self.assertEqual(
            evaluate_max_total_budget(requirement, PropertyData(price={"total": 4300})),
            0.0,
        )

    def test_area_reads_canonical_property_field(self):
        requirement = Requirement(value=40, is_strict_requirement=False)
        offer = PropertyData(area_sqm=45, parameters={"unexpected label": "1"})

        self.assertEqual(evaluate_min_area(requirement, offer), 1.0)

    def test_floor_preference_uses_structured_values_only(self):
        requirement = Requirement(
            value=FloorPreference(min_floor=2, max_floor=5, excluded_floors=[4]),
            is_strict_requirement=True,
        )

        self.assertEqual(
            evaluate_floor_preference(requirement, PropertyData(floor=3)),
            1.0,
        )
        self.assertEqual(
            evaluate_floor_preference(requirement, PropertyData(floor=4)),
            0.0,
        )

    def test_boolean_requirement_uses_canonical_field(self):
        requirement = Requirement(value=True, is_strict_requirement=True)

        self.assertEqual(
            evaluate_has_balcony(requirement, PropertyData(has_balcony=False)),
            0.0,
        )


class CompareOfferTests(unittest.IsolatedAsyncioTestCase):
    async def test_manager_combines_structured_evaluators(self):
        offer = PropertyData(
            price={"total": 3900},
            area_sqm=45,
            rooms_count=2,
            max_tenants=2,
        )

        self.assertEqual(await compare_offer(_requirements(), offer), (1.0, 1.0))

    async def test_strict_failure_zeroes_only_factual_score(self):
        offer = PropertyData(
            price={"total": 4300},
            area_sqm=45,
            rooms_count=2,
            max_tenants=2,
        )

        factual, potential = await compare_offer(
            _requirements(strict_budget=True),
            offer,
        )

        self.assertEqual(factual, 0.0)
        self.assertEqual(potential, 0.75)

    async def test_semantic_field_falls_back_to_universal_ai_evaluator(self):
        offer = PropertyData(
            price={"total": 3900},
            area_sqm=45,
            rooms_count=2,
            max_tenants=2,
        )

        with patch(
            "services.matching.evaluate_with_ai",
            new=AsyncMock(return_value=0.8),
        ) as ai_evaluator:
            factual, potential = await compare_offer(
                _requirements(kitchen_type="Separate"),
                offer,
            )

        self.assertAlmostEqual(factual, 0.96)
        self.assertAlmostEqual(potential, 0.96)
        ai_evaluator.assert_awaited_once()
        self.assertEqual(ai_evaluator.await_args.args[1], "kitchen type")


if __name__ == "__main__":
    unittest.main()
