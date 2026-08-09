import re
from typing import Any


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:[.,]\d+)?", str(value).replace(" ", ""))
    return float(match.group(0).replace(",", ".")) if match else None


def parse_integer(value: Any) -> int | None:
    number = parse_number(value)
    return int(number) if number is not None else None


def parse_polish_boolean(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    normalized = str(value).strip().casefold()
    if normalized in {"tak", "yes", "true", "1"}:
        return True
    if normalized in {"nie", "no", "false", "0", "brak"}:
        return False
    return None


def normalize_olx_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    """Map exact OLX labels to canonical PropertyData fields."""
    amenities = parameters.get("Wyposażenie")
    return {
        "area_sqm": parse_number(parameters.get("Powierzchnia")),
        "rooms_count": parse_integer(parameters.get("Liczba pokoi")),
        "floor": parse_integer(parameters.get("Poziom")),
        "building_floors": parse_integer(parameters.get("Liczba pięter")),
        "has_balcony": parse_polish_boolean(parameters.get("Balkon")),
        "pets_allowed": parse_polish_boolean(parameters.get("Zwierzęta")),
        "furnished": parse_polish_boolean(parameters.get("Umeblowane")),
        "elevator": parse_polish_boolean(parameters.get("Winda")),
        "parking": parameters.get("Parking"),
        "building_type": parameters.get("Rodzaj zabudowy"),
        "condition": parameters.get("Stan wykończenia"),
        "heating": parameters.get("Ogrzewanie"),
        "amenities": amenities if isinstance(amenities, list) else [],
    }


def normalize_otodom_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    """Map exact Otodom characteristic keys to canonical PropertyData fields."""
    return {
        "area_sqm": parse_number(parameters.get("m")),
        "rooms_count": parse_integer(parameters.get("rooms_num")),
        "floor": parse_integer(parameters.get("floor_no")),
        "building_floors": parse_integer(parameters.get("building_floors_num")),
        "has_balcony": parse_polish_boolean(parameters.get("balcony")),
        "furnished": parse_polish_boolean(parameters.get("furniture")),
        "elevator": parse_polish_boolean(parameters.get("lift")),
        "parking": parameters.get("parking"),
        "building_type": parameters.get("building_type"),
        "condition": parameters.get("building_ownership"),
        "heating": parameters.get("heating"),
    }
