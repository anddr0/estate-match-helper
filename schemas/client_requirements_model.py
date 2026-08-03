from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar('T')

class Requirement(BaseModel, Generic[T]):
	value: T
	is_strict_requirement: bool = Field(default=False)


class AdditionalPreferences(BaseModel):
	floor_preferences: Requirement[str | None] | None = None
	design_style: Requirement[str | None] | None = None
	has_balcony: Requirement[bool | None] | None = None
	other: Requirement[str | None] | None = None

class CurrentApartmentFeedback(BaseModel):
	liked: str | None = None
	disliked: str | None = None

class PropertyRequirements(BaseModel):
	min_area_sqm: Requirement[Annotated[float | None, Field(ge=0)]] | None = None
	min_functional_requirements: Requirement[str | None] | None = None
	rooms_count: Requirement[Annotated[int | None, Field(ge=1)]]
	kitchen_type: Requirement[str | None] | None = None
	building_disqualifiers: Requirement[list[str]] | None = None
	additional_preferences: AdditionalPreferences | None = None
	current_apartment_feedback: CurrentApartmentFeedback | None = None

class Commute(BaseModel):
	optimal_time_minutes: Requirement[int | None] | None = None
	max_time_minutes: Requirement[int | None] | None = None
	max_distance_km: Requirement[float | None] | None = None

class Location(BaseModel):
	anchor_points: Requirement[list[str]] | None = None
	transportation_type: Requirement[str | None] | None = None
	commute: Commute | None = None
	infrastructure_preferences: Requirement[list[str]] | None = None

class TenantsProfile(BaseModel):
	adults_count: int = Field(ge=1)
	children_count: int | None = Field(default=None, ge=0)
	pets: Requirement[str | None] | None = None
	details: str | None = None

class FinancialSituation(BaseModel):
	occupations: str | None = None
	employed_tenants_info: str | None = None
	income_proof_documents: list[str] | None = None

class Budget(BaseModel):
	max_total_budget_pln: Requirement[float | None]
	base_rent_pln: Requirement[float | None] | None = None
	includes_admin_fees: bool | None = None

class PersonalSituation(BaseModel):
	tenants_profile: TenantsProfile
	current_housing_status: str | None = None
	lease_period_expectations: Requirement[str | None] | None = None
	financial_situation: FinancialSituation | None = None
	budget: Budget

class ClientRentalRequirements(BaseModel):
	property_requirements: PropertyRequirements
	location: Location
	personal_situation: PersonalSituation
	summary: str | None = None
