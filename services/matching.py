import math
from collections.abc import Iterable
from typing import TypeAlias

from schemas.client_requirements import (
    ClientRentalRequirements,
    FloorPreference,
    Requirement,
)
from schemas.property import PropertyData
from services.matching_ai import evaluate_with_ai

Score: TypeAlias = float | None


def _has_value(requirement: Requirement | None) -> bool:
    if requirement is None or requirement.value is None:
        return False
    return requirement.value not in ("", [])


def _respect_strictness(requirement: Requirement, score: float) -> float:
    score = min(1.0, max(0.0, score))
    if requirement.is_strict_requirement and score < 1.0:
        return 0.0
    return score


def _score_maximum(requirement: Requirement, actual: float | None) -> Score:
    if not _has_value(requirement) or actual is None:
        return None
    maximum = float(requirement.value)
    if actual <= maximum:
        return 1.0
    relative_overage = (actual - maximum) / max(maximum, 1.0)
    return _respect_strictness(requirement, math.exp(-9 * relative_overage))


def _score_minimum(requirement: Requirement, actual: float | None) -> Score:
    if not _has_value(requirement) or actual is None:
        return None
    minimum = float(requirement.value)
    if actual >= minimum:
        return 1.0
    relative_shortfall = (minimum - actual) / max(minimum, 1.0)
    return _respect_strictness(requirement, math.exp(-9 * relative_shortfall))


def _score_boolean(requirement: Requirement, actual: bool | None) -> Score:
    if not _has_value(requirement) or actual is None:
        return None
    score = 1.0 if bool(requirement.value) == actual else 0.25
    return _respect_strictness(requirement, score)


async def _evaluate_semantic_requirement(
    requirement: Requirement | None,
    offer: PropertyData,
    name: str,
    instructions: str,
) -> Score:
    if not _has_value(requirement):
        return None
    score = await evaluate_with_ai(offer, name, requirement.value, instructions)
    return None if score is None else _respect_strictness(requirement, score)


def evaluate_min_area(requirement: Requirement, offer: PropertyData) -> Score:
    return _score_minimum(requirement, offer.area_sqm)


async def evaluate_min_functional_requirements(
    requirement: Requirement | None,
    offer: PropertyData,
) -> Score:
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "minimum functional requirements",
        "Check whether the layout, rooms, amenities and description provide the requested functions.",
    )


def evaluate_rooms_count(requirement: Requirement, offer: PropertyData) -> Score:
    if not _has_value(requirement) or offer.rooms_count is None:
        return None
    difference = abs(int(requirement.value) - offer.rooms_count)
    score = 1.0 if difference == 0 else math.exp(-0.7 * difference)
    return _respect_strictness(requirement, score)


async def evaluate_kitchen_type(
    requirement: Requirement | None,
    offer: PropertyData,
) -> Score:
    if not _has_value(requirement) or requirement.value == "Any":
        return None
    if offer.kitchen_type is not None:
        score = 1.0 if offer.kitchen_type == requirement.value else 0.25
        return _respect_strictness(requirement, score)
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "kitchen type",
        "Infer the kitchen type from the title, description and available property facts.",
    )


async def evaluate_building_disqualifiers(
    requirement: Requirement | None,
    offer: PropertyData,
) -> Score:
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "building disqualifiers",
        "Return 1 only when none of the listed disqualifying conditions applies to the building.",
    )


def evaluate_floor_preference(
    requirement: Requirement[FloorPreference | None] | None,
    offer: PropertyData,
) -> Score:
    if not _has_value(requirement) or offer.floor is None:
        return None
    preference = requirement.value
    scores: list[float] = []
    if preference.min_floor is not None:
        scores.append(1.0 if offer.floor >= preference.min_floor else 0.25)
    if preference.max_floor is not None:
        scores.append(1.0 if offer.floor <= preference.max_floor else 0.25)
    if preference.excluded_floors:
        scores.append(0.25 if offer.floor in preference.excluded_floors else 1.0)
    if not scores:
        return None
    return _respect_strictness(requirement, sum(scores) / len(scores))


async def evaluate_design_style(
    requirement: Requirement | None,
    offer: PropertyData,
) -> Score:
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "design style",
        "Assess the requested design and finish using the description and structured condition data.",
    )


def evaluate_has_balcony(requirement: Requirement | None, offer: PropertyData) -> Score:
    return _score_boolean(requirement, offer.has_balcony)


async def evaluate_other_preferences(
    requirement: Requirement | None,
    offer: PropertyData,
) -> Score:
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "other property preferences",
        "Evaluate only the additional preferences stated in the requirement.",
    )


async def evaluate_current_apartment_likes(value: str | None, offer: PropertyData) -> Score:
    if not value:
        return None
    return await evaluate_with_ai(
        offer,
        "features liked in current apartment",
        value,
        "Score whether the offer preserves the features the tenant currently likes.",
    )


async def evaluate_current_apartment_dislikes(value: str | None, offer: PropertyData) -> Score:
    if not value:
        return None
    return await evaluate_with_ai(
        offer,
        "features disliked in current apartment",
        value,
        "Score 1 when the offer avoids the disliked features and 0 when it repeats them.",
    )


async def evaluate_anchor_points(requirement: Requirement | None, offer: PropertyData) -> Score:
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "location anchor points",
        "Assess whether the offer location is suitable relative to the requested anchor points.",
    )


async def evaluate_transportation_type(
    requirement: Requirement | None,
    offer: PropertyData,
) -> Score:
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "transportation type",
        "Assess access to the requested means of transportation from the offer location.",
    )


async def evaluate_optimal_commute_time(
    requirement: Requirement | None,
    offer: PropertyData,
) -> Score:
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "optimal commute time in minutes",
        "Estimate commute suitability using the location, anchor points and transportation context.",
    )


async def evaluate_max_commute_time(
    requirement: Requirement | None,
    offer: PropertyData,
) -> Score:
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "maximum commute time in minutes",
        "Return 1 when the maximum commute is respected; degrade the score when it is exceeded.",
    )


async def evaluate_max_distance(
    requirement: Requirement | None,
    offer: PropertyData,
) -> Score:
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "maximum distance in kilometres",
        "Assess distance from the offer to the requested anchor points without inventing coordinates.",
    )


async def evaluate_infrastructure_preferences(
    requirement: Requirement | None,
    offer: PropertyData,
) -> Score:
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "infrastructure preferences",
        "Check requested nearby infrastructure against the location and description.",
    )


async def evaluate_adults_count(adults_count: int, offer: PropertyData) -> Score:
    if offer.max_tenants is not None:
        return 1.0 if adults_count <= offer.max_tenants else 0.0
    return await evaluate_with_ai(
        offer,
        "adult tenants count",
        adults_count,
        "Check whether the landlord allows this number of adult tenants.",
    )


async def evaluate_children_count(children_count: int | None, offer: PropertyData) -> Score:
    if children_count is None or children_count == 0:
        return None
    if offer.children_allowed is not None:
        return 1.0 if offer.children_allowed else 0.0
    return await evaluate_with_ai(
        offer,
        "children count",
        children_count,
        "Check whether the offer accepts a household with this number of children.",
    )


async def evaluate_pets(requirement: Requirement | None, offer: PropertyData) -> Score:
    if not _has_value(requirement):
        return None
    if offer.pets_allowed is not None:
        score = 1.0 if offer.pets_allowed else 0.0
        return _respect_strictness(requirement, score)
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "pets",
        "Check whether the described pets are accepted by the landlord.",
    )


async def evaluate_tenant_details(value: str | None, offer: PropertyData) -> Score:
    if not value:
        return None
    return await evaluate_with_ai(
        offer,
        "tenant profile details",
        value,
        "Check explicit landlord restrictions relevant to these tenant details.",
    )


async def evaluate_current_housing_status(value: str | None, offer: PropertyData) -> Score:
    if not value:
        return None
    return await evaluate_with_ai(
        offer,
        "current housing status",
        value,
        "Check only whether this status conflicts with explicit offer or landlord conditions.",
    )


async def evaluate_lease_period(
    requirement: Requirement | None,
    offer: PropertyData,
) -> Score:
    return await _evaluate_semantic_requirement(
        requirement,
        offer,
        "lease period expectations",
        "Compare the requested lease period with explicit duration conditions in the offer.",
    )


async def evaluate_occupations(value: str | None, offer: PropertyData) -> Score:
    if not value:
        return None
    return await evaluate_with_ai(
        offer,
        "tenant occupations",
        value,
        "Check explicit landlord restrictions concerning occupation or employment.",
    )


async def evaluate_employed_tenants_info(value: str | None, offer: PropertyData) -> Score:
    if not value:
        return None
    return await evaluate_with_ai(
        offer,
        "employed tenants information",
        value,
        "Check whether employment-related landlord conditions can be met.",
    )


async def evaluate_income_proof_documents(
    value: list[str] | None,
    offer: PropertyData,
) -> Score:
    if not value:
        return None
    return await evaluate_with_ai(
        offer,
        "available income proof documents",
        value,
        "Check whether the available documents satisfy explicit landlord requirements.",
    )


def evaluate_max_total_budget(requirement: Requirement, offer: PropertyData) -> Score:
    total = offer.price.total if offer.price else None
    return _score_maximum(requirement, total)


def evaluate_base_rent(requirement: Requirement | None, offer: PropertyData) -> Score:
    base_rent = offer.price.rent if offer.price else None
    return _score_maximum(requirement, base_rent)


def evaluate_admin_fees_inclusion(value: bool | None, offer: PropertyData) -> Score:
    if value is None or offer.price is None or offer.price.includes_admin_fees is None:
        return None
    return 1.0 if value == offer.price.includes_admin_fees else 0.25


async def evaluate_summary(value: str | None, offer: PropertyData) -> Score:
    if not value:
        return None
    return await evaluate_with_ai(
        offer,
        "client requirements summary",
        value,
        "Use the summary only for important intent not already represented by structured checks.",
    )


def _average(scores: Iterable[Score]) -> float:
    evaluated_scores = [score for score in scores if score is not None]
    return sum(evaluated_scores) / len(evaluated_scores) if evaluated_scores else 0.0


def _strict_requirement_failed(
    requirement: Requirement | None,
    score: Score,
) -> bool:
    return bool(
        _has_value(requirement)
        and requirement.is_strict_requirement
        and score is not None
        and score < 1.0
    )


async def compare_offer(
    client_requirements: ClientRentalRequirements,
    offer: PropertyData,
) -> tuple[float, float]:
    """Evaluate every client requirement and return factual/potential scores."""
    property_requirements = client_requirements.property_requirements
    preferences = property_requirements.additional_preferences
    feedback = property_requirements.current_apartment_feedback
    location = client_requirements.location
    commute = location.commute
    situation = client_requirements.personal_situation
    tenants = situation.tenants_profile
    finances = situation.financial_situation
    budget = situation.budget

    min_area = evaluate_min_area(property_requirements.min_area_sqm, offer)
    functionality = await evaluate_min_functional_requirements(
        property_requirements.min_functional_requirements, offer
    )
    rooms = evaluate_rooms_count(property_requirements.rooms_count, offer)
    kitchen = await evaluate_kitchen_type(property_requirements.kitchen_type, offer)
    building = await evaluate_building_disqualifiers(
        property_requirements.building_disqualifiers, offer
    )

    floor = evaluate_floor_preference(preferences.floor_preferences if preferences else None, offer)
    design = await evaluate_design_style(preferences.design_style if preferences else None, offer)
    balcony = evaluate_has_balcony(preferences.has_balcony if preferences else None, offer)
    other = await evaluate_other_preferences(preferences.other if preferences else None, offer)

    liked = await evaluate_current_apartment_likes(feedback.liked if feedback else None, offer)
    disliked = await evaluate_current_apartment_dislikes(feedback.disliked if feedback else None, offer)

    anchors = await evaluate_anchor_points(location.anchor_points, offer)
    transport = await evaluate_transportation_type(location.transportation_type, offer)
    optimal_commute = await evaluate_optimal_commute_time(
        commute.optimal_time_minutes if commute else None, offer
    )
    max_commute = await evaluate_max_commute_time(
        commute.max_time_minutes if commute else None, offer
    )
    max_distance = await evaluate_max_distance(commute.max_distance_km if commute else None, offer)
    infrastructure = await evaluate_infrastructure_preferences(
        location.infrastructure_preferences, offer
    )

    adults = await evaluate_adults_count(tenants.adults_count, offer)
    children = await evaluate_children_count(tenants.children_count, offer)
    pets = await evaluate_pets(tenants.pets, offer)
    tenant_details = await evaluate_tenant_details(tenants.details, offer)

    housing_status = await evaluate_current_housing_status(situation.current_housing_status, offer)
    lease_period = await evaluate_lease_period(situation.lease_period_expectations, offer)
    occupations = await evaluate_occupations(finances.occupations if finances else None, offer)
    employment = await evaluate_employed_tenants_info(
        finances.employed_tenants_info if finances else None, offer
    )
    income_documents = await evaluate_income_proof_documents(
        finances.income_proof_documents if finances else None, offer
    )

    total_budget = evaluate_max_total_budget(budget.max_total_budget_pln, offer)
    base_rent = evaluate_base_rent(budget.base_rent_pln, offer)
    admin_fees = evaluate_admin_fees_inclusion(budget.includes_admin_fees, offer)
    summary = await evaluate_summary(client_requirements.summary, offer)

    scores = (
        min_area, functionality, rooms, kitchen, building,
        floor, design, balcony, other, liked, disliked,
        anchors, transport, optimal_commute, max_commute, max_distance, infrastructure,
        adults, children, pets, tenant_details, housing_status, lease_period,
        occupations, employment, income_documents,
        total_budget, base_rent, admin_fees, summary,
    )
    potential_score = _average(scores)

    strict_results = (
        (property_requirements.min_area_sqm, min_area),
        (property_requirements.min_functional_requirements, functionality),
        (property_requirements.rooms_count, rooms),
        (property_requirements.kitchen_type, kitchen),
        (property_requirements.building_disqualifiers, building),
        (preferences.floor_preferences if preferences else None, floor),
        (preferences.design_style if preferences else None, design),
        (preferences.has_balcony if preferences else None, balcony),
        (preferences.other if preferences else None, other),
        (location.anchor_points, anchors),
        (location.transportation_type, transport),
        (commute.optimal_time_minutes if commute else None, optimal_commute),
        (commute.max_time_minutes if commute else None, max_commute),
        (commute.max_distance_km if commute else None, max_distance),
        (location.infrastructure_preferences, infrastructure),
        (tenants.pets, pets),
        (situation.lease_period_expectations, lease_period),
        (budget.max_total_budget_pln, total_budget),
        (budget.base_rent_pln, base_rent),
    )
    factual_score = (
        0.0
        if any(_strict_requirement_failed(requirement, score) for requirement, score in strict_results)
        else potential_score
    )
    return factual_score, potential_score
