import os
from bs4 import BeautifulSoup


class BaseParser:
	def __init__(self, source):
		self.html_content = self._load_content(source)
		self.soup = BeautifulSoup(self.html_content, 'html.parser')

	def _load_content(self, source):
		try:
			is_file = os.path.isfile(source)
		except (ValueError, TypeError, OSError):
			is_file = False

		if is_file:
			with open(source, 'r', encoding='utf-8') as f:
				return f.read()

		return source

	def parse(self):
		raise NotImplementedError("Метод parse() должен быть реализован в дочернем классе.")