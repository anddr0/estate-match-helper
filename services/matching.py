import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from schemas.client_requirements import ClientRentalRequirements, Requirement
from schemas.property import PropertyData


@dataclass(frozen=True)
class _Check:
    matches: bool
    is_strict: bool


def _number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"\d+(?:[.,]\d+)?", str(value).replace(" ", ""))
    return float(match.group(0).replace(",", ".")) if match else None


def _normalized_parameters(offer: PropertyData) -> dict[str, Any]:
    return {
        str(key).strip().casefold(): value
        for key, value in (offer.parameters or {}).items()
    }


def _find_parameter(parameters: dict[str, Any], names: Iterable[str]) -> Any:
    normalized_names = tuple(name.casefold() for name in names)
    for key, value in parameters.items():
        if any(name in key for name in normalized_names):
            return value
    return None


def _add_check(
    checks: list[_Check],
    requirement: Requirement | None,
    offer_value: Any,
    predicate: Callable[[Any, Any], bool],
) -> None:
    if requirement is None or requirement.value is None or offer_value is None:
        return
    checks.append(
        _Check(
            predicate(requirement.value, offer_value),
            requirement.is_strict_requirement,
        )
    )


def compare_offer(
    client_requirements: ClientRentalRequirements,
    offer: PropertyData,
    ai_score: float | None = None,
) -> tuple[float, float]:
    """Return factual and non-disqualified scores in the 0..1 range.

    Structured fields are checked in code. Textual criteria can later be scored
    by AI and supplied as ``ai_score``. A confirmed strict failure makes the
    factual score zero, while the second score preserves the underlying quality.
    Missing offer data is left for enrichment or AI instead of causing rejection.
    """
    if ai_score is not None and not 0 <= ai_score <= 1:
        raise ValueError("ai_score must be between 0 and 1")

    checks: list[_Check] = []
    parameters = _normalized_parameters(offer)
    property_requirements = client_requirements.property_requirements
    budget = client_requirements.personal_situation.budget

    total_price = _number(offer.price.total) if offer.price else None
    _add_check(
        checks,
        budget.max_total_budget_pln,
        total_price,
        lambda required, actual: actual <= float(required),
    )

    area = _number(_find_parameter(parameters, ("area", "powierzchnia")))
    _add_check(
        checks,
        property_requirements.min_area_sqm,
        area,
        lambda required, actual: actual >= float(required),
    )

    rooms = _number(_find_parameter(parameters, ("rooms", "liczba pokoi", "pokoj")))
    _add_check(
        checks,
        property_requirements.rooms_count,
        rooms,
        lambda required, actual: int(actual) == int(required),
    )

    preferences = property_requirements.additional_preferences
    balcony_requirement = preferences.has_balcony if preferences else None
    balcony = _find_parameter(parameters, ("balcony", "balkon"))
    if balcony is not None:
        balcony_value = str(balcony).casefold() not in {
            "false",
            "no",
            "nie",
            "brak",
            "0",
        }
        _add_check(
            checks,
            balcony_requirement,
            balcony_value,
            lambda required, actual: bool(required) == actual,
        )

    components = [1.0 if check.matches else 0.0 for check in checks]
    if ai_score is not None:
        components.append(ai_score)
    potential_score = sum(components) / len(components) if components else 0.0

    has_strict_failure = any(check.is_strict and not check.matches for check in checks)
    factual_score = 0.0 if has_strict_failure else potential_score
    return factual_score, potential_score
