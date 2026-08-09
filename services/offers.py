import asyncio
from dataclasses import dataclass

from loguru import logger

from parsers.offer_links import OfferLinksParser
from parsers.router import parse_property_url
from schemas.client_requirements import ClientRentalRequirements
from services.matching import compare_offer


@dataclass(frozen=True)
class LinkEvaluation:
    url: str
    factual_score: float | None = None
    potential_score: float | None = None
    error: str | None = None


def extract_offer_links(html_content: str) -> list[str]:
    return OfferLinksParser(html_content).parse()


async def evaluate_offer(
    url: str,
    client_requirements: ClientRentalRequirements,
) -> LinkEvaluation:
    try:
        parsed_response = await asyncio.to_thread(parse_property_url, url)
        factual_score, potential_score = compare_offer(
            client_requirements,
            parsed_response.data,
        )
        return LinkEvaluation(
            url=url,
            factual_score=factual_score,
            potential_score=potential_score,
        )
    # One failed URL must not cancel the whole batch. This boundary deliberately
    # converts parser, validation and network failures into a per-link result.
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"Ошибка обработки оферты {url}: {exc}")
        return LinkEvaluation(url=url, error=str(exc))


async def evaluate_offers(
    urls: list[str],
    client_requirements: ClientRentalRequirements,
) -> list[LinkEvaluation]:
    tasks = [evaluate_offer(url, client_requirements) for url in urls]
    return await asyncio.gather(*tasks)
