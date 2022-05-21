import json
from pprint import pprint

import requests

search_requests = [
    "террор дэн симмонс",
    "яма куприн",
    "заводной апельсин",
    "стивенсон ртуть",
    "обитатели холмов",
    "гордость и предубеждение",
    "женщина в белом",
    "гипперион",
    "978-5-389-05734-0",
    "Оно",
    "звездные войны"
]


class OzonParser:
    # характеристики так же включают: Publisher, Seria, CoverPersons, BookType, Translator, AgeConsumer,
    # Format, WeightPack
    fields_for_parse = {'Writer': 'author',
                        'ReleaseYear': 'year_of_publication',
                        'CoverType': 'type_of_cover',
                        'ISBN': 'ISBN',
                        'Language': 'language',
                        'PageCount': 'pages', }

    def __init__(self, search_request):
        self.book_info = dict()
        self.search_request = search_request
        self.characteristics = None

    @staticmethod
    def get_search_url(search_request):
        return ("https://www.ozon.ru/api/composer-api.bx/page/json/v2"
                "?url=/searchSuggestions/?from_global=true&text="
                f"{search_request.replace(' ', '+')}")

    @staticmethod
    def get_product_url(product_parsed_name):
        return ("https://www.ozon.ru/api/composer-api.bx/page/json/v2"
                f"?url=/product/{product_parsed_name}/"
                "&layout_container=pdpPage2column"
                "&layout_page_index=2")

    def parse_product_for_query(self):
        response = requests.get(self.get_search_url(self.search_request))
        data = response.json()
        for key, value in data['widgetStates'].items():
            for item in json.loads(value)['items']:
                if item['link'].startswith('/product/'):
                    self.book_info['title'] = item['title'].split('|')[0].strip()
                    return item['link'].split('/')[-2]

    def parse_book_info(self):
        product_parsed_name = self.parse_product_for_query()
        product_url = self.get_product_url(product_parsed_name)
        response = requests.get(product_url)
        data = response.json()
        for key, value in data['widgetStates'].items():
            if all(x in value for x in (product_parsed_name, 'BookType')):
                self.characteristics = json.loads(value)['characteristics'][0]['short']
            if 'richAnnotation' in value:
                self.book_info['annotation'] = self.remove_html_tags(json.loads(value)['richAnnotation'])

    def extract_fields(self):
        self.parse_book_info()
        book_fields = dict()
        for value in self.characteristics:
            if value['key'] in self.fields_for_parse.keys():
                book_fields.update({self.fields_for_parse[value['key']]: value["values"][0]["text"]})
        self.book_info.update(book_fields)
        if not self.search_request.replace(' ', '').isalnum():
            self.book_info = {key: self.book_info[key] for key in ['title', 'annotation', 'author']}

    @staticmethod
    def remove_html_tags(text):
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)


if __name__ == '__main__':
    for query in search_requests:
        parser = OzonParser(query)
        try:
            parser.extract_fields()
        except Exception as e:
            parser.book_info.clear()
