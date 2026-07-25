from parsers.base_parser import BaseParser


class SadsParser(BaseParser):
    def parse(self):
        all_links = []
        for a_tag in self.soup.find_all('a', string="Źródło oferty"):
            href = a_tag.get('href')
            if href:
                all_links.append(href)

        return all_links