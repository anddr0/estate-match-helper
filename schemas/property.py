from pydantic import BaseModel, Field


class PriceData(BaseModel):
    total: float | None = None
    currency: str | None = None
    per_m2: float | None = None
    rent: float | None = None
    admin_fees: float | None = None
    includes_admin_fees: bool | None = None


class LocationData(BaseModel):
    city: str | None = None
    region: str | None = None
    subregion: str | None = None
    street: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class MetaData(BaseModel):
    created_at: str | None = None
    updated_at: str | None = None
    advertiser_type: str | None = None


class PropertyData(BaseModel):
    id: str | int | None = None
    public_id: str | None = None
    url: str | None = None
    title: str | None = None
    description: str | None = None

    price: PriceData | None = None
    location: LocationData | None = None

    # Canonical fields populated by site parsers. Matching code reads only these
    # fields and never needs to know source-specific labels.
    area_sqm: float | None = Field(default=None, ge=0)
    rooms_count: int | None = Field(default=None, ge=1)
    floor: int | None = None
    building_floors: int | None = Field(default=None, ge=1)
    kitchen_type: str | None = None
    has_balcony: bool | None = None
    pets_allowed: bool | None = None
    max_tenants: int | None = Field(default=None, ge=1)
    children_allowed: bool | None = None
    lease_period_months: int | None = Field(default=None, ge=1)
    furnished: bool | None = None
    elevator: bool | None = None
    parking: str | None = None
    building_type: str | None = None
    condition: str | None = None
    heating: str | None = None
    amenities: list[str] = Field(default_factory=list)

    # Kept for diagnostics and AI context, not for matching lookups.
    parameters: dict[str, str | list[str]] = Field(default_factory=dict)
    images: list[str] | None = None
    meta: MetaData | None = None


class ParsedPropertyResponse(BaseModel):
    status: str
    data: PropertyData | None = None
    error: str | None = None
