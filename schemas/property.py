from pydantic import BaseModel
from typing import Optional, Dict, List, Union, Any


class OtodomRequest(BaseModel):
    url: str


class PriceData(BaseModel):
    total: Optional[Union[float, int, str]] = None
    currency: Optional[str] = None
    per_m2: Optional[Union[float, int, str]] = None
    rent: Optional[Union[float, int, str]] = None


class LocationData(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    subregion: Optional[str] = None
    street: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class MetaData(BaseModel):
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    advertiser_type: Optional[str] = None


class PropertyData(BaseModel):
    id: Optional[Union[str, int]] = None
    public_id: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    price: Optional[PriceData] = None
    location: Optional[LocationData] = None

    parameters: Optional[Dict[str, Union[str, List[str]]]] = None
    images: Optional[List[str]] = None
    meta: Optional[MetaData] = None


class ParsedPropertyResponse(BaseModel):
    status: str
    data: Optional[PropertyData] = None
    error: Optional[str] = None