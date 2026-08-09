import os

from bs4 import BeautifulSoup


class BaseParser:
    def __init__(self, source):
        self.html_content = self._load_content(source)
        self.soup = BeautifulSoup(self.html_content, "html.parser")

    @staticmethod
    def _load_content(source):
        try:
            is_file = os.path.isfile(source)
        except (ValueError, TypeError, OSError):
            is_file = False

        if is_file:
            with open(source, encoding="utf-8") as file:
                return file.read()

        return source

    def parse(self):
        raise NotImplementedError("parse() must be implemented by a subclass")
