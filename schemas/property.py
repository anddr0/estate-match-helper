from pydantic import BaseModel


class OtodomRequest(BaseModel):
    url: str


class PriceData(BaseModel):
    total: float | int | str | None = None
    currency: str | None = None
    per_m2: float | int | str | None = None
    rent: float | int | str | None = None


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

    parameters: dict[str, str | list[str]] | None = None
    images: list[str] | None = None
    meta: MetaData | None = None


class ParsedPropertyResponse(BaseModel):
    status: str
    data: PropertyData | None = None
    error: str | None = None