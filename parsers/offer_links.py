from parsers.base import BaseParser


class OfferLinksParser(BaseParser):
    """Extract property source URLs from an exported SADS HTML page."""

    def parse(self) -> list[str]:
        return [
            anchor["href"]
            for anchor in self.soup.find_all("a", string="Źródło oferty")
            if anchor.get("href")
        ]
