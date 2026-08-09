import json

from loguru import logger

from parsers.base import BaseParser
from parsers.normalization import normalize_otodom_parameters
from schemas.property import ParsedPropertyResponse


class OtodomParser(BaseParser):
	def _extract_next_data(self):
		script_tag = self.soup.find('script', id='__NEXT_DATA__', type='application/json')
		if script_tag and script_tag.string:
			try:
				return json.loads(script_tag.string)
			except json.JSONDecodeError as e:
				logger.error(f"JSONDecodeError при разборе __NEXT_DATA__ в OtodomParser: {e}")
				return None
		logger.debug("Скрипт __NEXT_DATA__ не найден на странице Otodom.")
		return None

	def parse(self):
		logger.info("Начало парсинга страницы Otodom...")
		next_data = self._extract_next_data()

		if next_data:
			parsed_data = self._parse_from_json(next_data)
			if parsed_data:
				logger.success(f"Успешный парсинг Otodom из JSON (ID: {parsed_data.get('id')})")
				return ParsedPropertyResponse(status="success", data=parsed_data)

		logger.warning("Переход к резервному парсингу из HTML (fallback) для Otodom.")
		fallback_data = self._parse_from_html_fallback()
		logger.info("Завершен резервный парсинг из HTML.")
		if any(
			(
				fallback_data.get('id'),
				fallback_data.get('title'),
				fallback_data.get('description'),
				fallback_data.get('parameters'),
				fallback_data.get('price', {}).get('total'),
			)
		):
			return ParsedPropertyResponse(status="success", data=fallback_data)
		return ParsedPropertyResponse(
			status="error",
			error="Otodom data not found in HTML",
		)

	def _parse_from_json(self, next_data):
		ad_data = next_data.get('props', {}).get('pageProps', {}).get('ad', {})
		if not ad_data:
			logger.debug("Структура 'ad' отсутствует в __NEXT_DATA__")
			return None

		target_data = ad_data.get('target', {})

		parameters = {}
		for char in ad_data.get('characteristics', []):
			key = char.get('key')
			value = char.get('localizedValue') or char.get('value')
			if key and value:
				parameters[key] = value

		images = [img.get('large') for img in ad_data.get('images', []) if img.get('large')]
		canonical_parameters = normalize_otodom_parameters(parameters)

		return {
			'id': ad_data.get('id'),
			'public_id': ad_data.get('publicId') or ad_data.get('public_id'),
			'url': ad_data.get('url'),
			'title': ad_data.get('title'),
			'description': ad_data.get('description'),

			'price': {
				'total': target_data.get('Price'),
				'currency': target_data.get('Currency') or 'PLN',
				'per_m2': target_data.get('Price_per_m'),
				'rent': target_data.get('Rent'),
			},

			'location': {
				'city': target_data.get('City'),
				'region': target_data.get('Province') or target_data.get('Region'),
				'subregion': target_data.get('Subregion'),
				'street': target_data.get('street_name'),
				'latitude': ad_data.get('location', {}).get('coordinates', {}).get('latitude'),
				'longitude': ad_data.get('location', {}).get('coordinates', {}).get('longitude'),
			},

			'parameters': parameters,
			**canonical_parameters,
			'images': images,

			'meta': {
				'created_at': ad_data.get('createdAt'),
				'updated_at': ad_data.get('modifiedAt'),
				'advertiser_type': target_data.get('user_type'),
			}
		}

	@staticmethod
	def clean_number(text):
		"""'533\xa0000 zł' → 533000.0"""
		if text is None:
			return None
		cleaned = str(text).replace('\xa0', '').replace(' ', '')
		cleaned = ''.join(c for c in cleaned if c.isdigit() or c in '.,')
		cleaned = cleaned.replace(',', '.')
		try:
			return float(cleaned)
		except ValueError:
			return None

	def _parse_from_html_fallback(self):
		return {
			'id': self._get_id_html(),
			'title': self._get_text_by_cy('adPageAdTitle'),
			'price': {
				'total': self.clean_number(
					self._get_text_by_cy('adPageHeaderPrice', remove_spaces=True)
				),
				'currency': 'PLN',
			},
			'location': {'subregion': self._get_location_html()},
			'description': self._get_text_by_cy('adPageAdDescription', separator='\n'),
			'parameters': self._get_parameters_html(),
		}

	def _get_text_by_cy(self, cy_attr, separator=' ', remove_spaces=False):
		el = self.soup.find(attrs={"data-cy": cy_attr})
		if not el:
			return None
		text = el.get_text(separator=separator, strip=True)
		return text.replace(' ', '') if remove_spaces else text

	def _get_location_html(self):
		el = self.soup.find('a', href="#map")
		return el.get_text(strip=True) if el else None

	def _get_id_html(self):
		for p in self.soup.find_all('p'):
			text = p.get_text(strip=True)
			if text.startswith('ID'):
				return text.split(':')[-1].strip()
		return None

	def _get_parameters_html(self):
		params = {}
		containers = self.soup.find_all('div', attrs={"data-sentry-element": "ItemGridContainer"})
		for container in containers:
			items = container.find_all('div', recursive=False)
			if len(items) == 2:
				key = items[0].get_text(strip=True).replace(':', '').strip()
				spans = items[1].find_all('span')
				if spans and len(spans) > 1:
					params[key] = [span.get_text(strip=True) for span in spans]
				else:
					params[key] = items[1].get_text(strip=True)
		return params
