import json

from loguru import logger

from parsers.base import BaseParser
from schemas.property import ParsedPropertyResponse


class OlxParser(BaseParser):
	def _extract_json_ld(self):
		script_tag = self.soup.find('script', type='application/ld+json')
		if script_tag and script_tag.string:
			try:
				return json.loads(script_tag.string)
			except json.JSONDecodeError as e:
				logger.error(f"JSONDecodeError при разборе JSON-LD в OlxParser: {e}")
				return None
		logger.debug("Скрипт application/ld+json не найден на странице.")
		return None

	def parse(self):
		logger.info("Начало парсинга страницы OLX...")
		json_ld = self._extract_json_ld()

		if json_ld:
			parsed_data = self._parse_hybrid(json_ld)
			if parsed_data:
				logger.success(f"Успешный парсинг объявления OLX (ID: {parsed_data.get('id')})")
				return ParsedPropertyResponse(status="success", data=parsed_data)

		logger.warning("Данные JSON-LD не найдены или не распарсены, возвращаем ошибку.")
		return ParsedPropertyResponse(
			status="error",
			error="JSON-LD data not found in HTML",
		)

	def _parse_hybrid(self, json_ld):
		offers = json_ld.get('offers', {})
		price_data = {
			'total': offers.get('price'),
			'currency': offers.get('priceCurrency') or 'PLN'
		}

		location_data = self._get_location_from_breadcrumbs()
		if not location_data.get('subregion'):
			location_data['subregion'] = offers.get('areaServed', {}).get('name')

		parameters = self._get_parameters_html()

		advertiser_type = parameters.pop('advertiser_type', None)
		meta_data = {
			'created_at': self._get_created_at_html(),
			'advertiser_type': advertiser_type
		}

		return {
			'id': json_ld.get('sku'),
			'url': json_ld.get('url'),
			'title': json_ld.get('name'),
			'description': json_ld.get('description'),

			'price': price_data,
			'location': location_data,
			'parameters': parameters,

			'images': (
				json_ld.get('image', [])
				if isinstance(json_ld.get('image'), list)
				else [json_ld['image']] if json_ld.get('image') else []
			),
			'meta': meta_data
		}

	def _get_location_from_breadcrumbs(self):
		location = {}
		breadcrumbs_list = self.soup.find('ol', attrs={"data-testid": "breadcrumbs"})

		if breadcrumbs_list:
			items = [li.get_text(strip=True) for li in breadcrumbs_list.find_all('li')]

			for item in items:
				if ' - ' in item:
					part = item.split(' - ')[-1].strip()
					if not location.get('region'):
						location['region'] = part
					elif not location.get('city'):
						location['city'] = part
					elif not location.get('subregion'):
						location['subregion'] = part

		return location

	def _get_parameters_html(self):
		params = {}
		container = self.soup.find(attrs={"data-testid": "ad-parameters-container"})

		if container:
			for p_tag in container.find_all('p'):
				text = p_tag.get_text(strip=True)
				if ':' in text:
					key, value = text.split(':', 1)
					params[key.strip()] = value.strip()
				elif text in ['Prywatne', 'Firmowe']:
					params['advertiser_type'] = text.strip()

		return params

	def _get_created_at_html(self):
		posted_at_el = self.soup.find(attrs={"data-testid": "ad-posted-at"})
		if posted_at_el:
			text = posted_at_el.get_text(strip=True)
			return text.replace('Dodane', '').replace('<!-- -->', '').strip()
		return None
