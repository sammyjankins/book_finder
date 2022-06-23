from pprint import pprint

import requests

search_requests = [
    'террор дэн симмонс',
    'яма куприн',
    'заводной апельсин',
    'стивенсон ртуть',
    'обитатели холмов',
    'гордость и предубеждение',
    'женщина в белом',
    'гипперион',
    '978-5-389-05734-0',
    'Оно',
    'звездные войны'
]


class GoogleRequestSearch:
    """
    Поиск данных в googleapis.com/books с помощью библиотеки requests
    """
    fields_for_parse = {'description': 'annotation',
                        'title': 'title',
                        'publishedDate': 'year_of_publication',
                        'language': 'language',
                        'pageCount': 'pages', }

    def __init__(self, search_request):
        self.book_info = dict()
        self.search_request = search_request.replace('-', '')
        self.characteristics = None
        self.volume_info = None

    def get_search_url(self):
        base_api_link = 'https://www.googleapis.com/books/v1/volumes?q='
        isbn_search = 'isbn:' if self.search_request.isdigit() else ''
        return f'{base_api_link}{isbn_search}{self.search_request.replace(" ", "+")}'

    def contains_similar_word(self, word, search_line):
        return any([self.distance(word, fragment) for fragment in search_line.split()])

    def check_correct_request(self, volume_title):
        if volume_title.lower().strip() in self.search_request.lower().strip():
            return True
        return any([self.contains_similar_word(word.lower(), self.search_request.lower())
                    for word in volume_title.lower().split()])

    def find_volume_in_results(self, data):
        if self.search_request.isdigit():
            self.volume_info = data['items'][0]['volumeInfo']
        else:
            for item in data['items']:
                if self.check_correct_request(item['volumeInfo']['title']):
                    self.volume_info = item['volumeInfo']
                    break

    def search(self):
        response = requests.get(self.get_search_url())
        data = response.json()

        self.find_volume_in_results(data)

        for key, value in self.fields_for_parse.items():
            self.book_info[value] = self.volume_info.get(key)

        self.book_info['author'] = ", ".join(self.volume_info["authors"])

        if identifier := self.volume_info.get('industryIdentifiers'):
            for item in identifier:
                if item['type'] == 'ISBN_13':
                    self.book_info["ISBN"] = item['identifier']

    def distance(self, a, b):
        """Расстояние Левенштейна для выявления похожих слов
        https://en.wikipedia.org/wiki/Levenshtein_distance"""
        n, m = len(a), len(b)
        if n > m:
            a, b = b, a
            n, m = m, n

        current_row = range(n + 1)
        for i in range(1, m + 1):
            previous_row, current_row = current_row, [i] + [0] * n
            for j in range(1, n + 1):
                add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
                if a[j - 1] != b[i - 1]:
                    change += 1
                current_row[j] = min(add, delete, change)

        return current_row[n] <= len(b) * 0.25

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ИТОГОВЫЙ СКРИПТ
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


if __name__ == '__main__':
    for line in search_requests:
        searcher = GoogleRequestSearch(line)
        searcher.search()
        pprint(searcher.book_info)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# =====================================================================================================================
# СЛОМАНОЕ
# =====================================================================================================================

# при использовании библиотеки requests, сайт проверяет капчей

# class OzonRequestParser:
#     """
#     Извлечение данных о книге путем обращения к api сайта ozon с помощью библиотеки requests
#     """
#     # характеристики так же включают: Publisher, Seria, CoverPersons, BookType, Translator, AgeConsumer,
#     # Format, WeightPack
#     fields_for_parse = {'Writer': 'author',
#                         'ReleaseYear': 'year_of_publication',
#                         'CoverType': 'type_of_cover',
#                         'ISBN': 'ISBN',
#                         'Language': 'language',
#                         'PageCount': 'pages', }
#
#     def __init__(self, search_request):
#         self.book_info = dict()
#         self.search_request = search_request
#         self.characteristics = None
#
#     @staticmethod
#     def get_search_url(search_request):
#         return ("https://www.ozon.ru/api/composer-api.bx/page/json/v2"
#                 "?url=/searchSuggestions/?text="
#                 f"{search_request.replace(' ', '+')}")
#
#     @staticmethod
#     def get_product_url(product_parsed_name):
#         return ("https://www.ozon.ru/api/composer-api.bx/page/json/v2"
#                 f"?url=/product/{product_parsed_name}/"
#                 "&layout_container=pdpPage2column"
#                 "&layout_page_index=2")
#
#     def parse_product_for_query(self):
#         response = requests.get(self.get_search_url(self.search_request))
#         data = response.json()
#         for key, value in data['widgetStates'].items():
#             for item in json.loads(value)['items']:
#                 if item['link'].startswith('/product/'):
#                     self.book_info['title'] = item['title'].split('|')[0].strip()
#                     return item['link'].split('/')[-2]
#
#     def parse_book_info(self):
#         product_parsed_name = self.parse_product_for_query()
#         product_url = self.get_product_url(product_parsed_name)
#         response = requests.get(product_url)
#         data = response.json()
#         for key, value in data['widgetStates'].items():
#             if all(x in value for x in (product_parsed_name, 'BookType')):
#                 self.characteristics = json.loads(value)['characteristics'][0]['short']
#             if 'richAnnotation' in value:
#                 self.book_info['annotation'] = self.remove_html_tags(json.loads(value)['richAnnotation'])
#
#     def extract_fields(self):
#         self.parse_book_info()
#         book_fields = dict()
#         for value in self.characteristics:
#             if value['key'] in self.fields_for_parse.keys():
#                 book_fields.update({self.fields_for_parse[value['key']]: value["values"][0]["text"]})
#         self.book_info.update(book_fields)
#         if not self.search_request.replace(' ', '').isalnum():
#             self.book_info = {key: self.book_info[key] for key in ['title', 'annotation', 'author']}
#
#     @staticmethod
#     def remove_html_tags(text):
#         import re
#         clean = re.compile('<.*?>')
#         return re.sub(clean, '', text)

# if __name__ == '__main__':
#     for query in search_requests:
#         parser = OzonRequestParser(query)
#         try:
#             parser.extract_fields()
#         except Exception as e:
#             print(e)
#             parser.book_info.clear()
#
#     for query in search_requests:
#         browser.get('https://www.ozon.ru/category/knigi-16500/?category_was_predicted=true&from_global=true&text='
#                     f'{query.replace(" ", "+")}')
#         product = browser.find_element(By.CLASS_NAME, 'i4t').get_attribute('href')
#         browser.get(product)
#     browser.quit()
#


# =====================================================================================================================

# периодически меняется структура страницы поиска, что делает фрагменты обращения к тегам и id неактуальными

# class OzonSeleniumParser:
#     """
#     Извлечение данных о книге путем парсинга сайта ozon с помощью selenium. Импользуемый браузер - Firefox
#     """
#     fields_for_parse = {'Writer': 'author',
#                         'ReleaseYear': 'year_of_publication',
#                         'CoverType': 'type_of_cover',
#                         'ISBN': 'ISBN',
#                         'Language': 'language',
#                         'PageCount': 'pages', }
#
#     def __init__(self):
#         self.book_info = dict()
#         self.options = Options()
#         self.options.headless = True
#         self.browser = webdriver.Firefox(options=self.options)
#
#     def get_product_url(self, query):
#         self.browser.get('https://www.ozon.ru/category/knigi-16500/?category_was_predicted=true&from_global=true&text='
#                          f'{query.replace(" ", "+")}')
#         return self.browser.find_element(By.CLASS_NAME, 'i4t').get_attribute('href')
#
#     def get_product_info(self, query):
#         product_url = self.get_product_url(query)
#         self.browser.get(product_url)
#
#         title = self.browser.find_element(By.CLASS_NAME, 'l7q').text
#         self.book_info['title'] = title.split('|')[0].strip()
#         print(self.book_info['title'])
#
#         annotation_div = self.browser.find_element(By.CLASS_NAME, 'uk3')
#         self.book_info['annotation'] = annotation_div.find_element(By.XPATH, './/div').text
#         print(self.book_info['annotation'])
#         characteristics = self.browser.find_elements(By.CLASS_NAME, 'kk6')
#         for item in characteristics:
#             print(item.find_element(By.XPATH, './/span[@class="kk5"]').text)
#         self.browser.quit()

# if __name__ == '__main__':
#
#     product = browser.find_element(By.CLASS_NAME, 'i4t').get_attribute('href')
#     browser.get(product)
#     title = browser.find_element(By.CLASS_NAME, 'l7q')
#     print(title.text)
#
#     parser = OzonSeleniumParser()
#     parser.get_product_info(search_requests[0])

# =====================================================================================================================

# не удалось настроить совместимость браузеров и драйверов на сервере
# периодически меняется структура респонса, что делает фрагменты, связанные с извлечением данных, неактуальными

# import json
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.firefox.options import Options
# from pprint import pprint
# from multiprocessing.managers import BaseManager
# from time import sleep

# class ParseManager(BaseManager):
#     pass
#
#
# class OzonSeleniumForeverParser:
#     """
#     Извлечение данных о книге путем обращения к api сайта ozon с помощью selenium. Импользуемый браузер - Firefox
#     """
#     # характеристики так же включают: Publisher, Seria, CoverPersons, BookType, Translator, AgeConsumer,
#     # Format, WeightPack
#     fields_for_parse = {'Writer': 'author',
#                         'ReleaseYear': 'year_of_publication',
#                         'CoverType': 'type_of_cover',
#                         'ISBN': 'ISBN',
#                         'Language': 'language',
#                         'PageCount': 'pages', }
#
#     def __init__(self, search_request, browser_instance):
#         self.book_info = dict()
#         self.search_request = search_request
#         self.characteristics = None
#         self.browser = browser_instance
#
#     @staticmethod
#     def get_search_url(search_request):
#         return ("https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=/category/knigi-16500/search/?text="
#                 f"{search_request.replace(' ', '+')}")
#
#     @staticmethod
#     def get_product_url(product_parsed_name):
#         return ("https://www.ozon.ru/api/composer-api.bx/page/json/v2"
#                 f"?url=/product/{product_parsed_name}/"
#                 "&layout_container=pdpPage2column"
#                 "&layout_page_index=2")
#
#     def parse_product_for_query(self):
#         self.browser.get(self.get_search_url(self.search_request))
#         content = self.browser.find_element(By.TAG_NAME, 'body').text
#         data = json.loads(content)
#         for key, value in data['widgetStates'].items():
#             if 'searchResultsV2' in key:
#                 item = json.loads(value)['items'][0]
#                 self.extract_title(item)
#                 return item['action']['link'].split('/')[-2]
#
#     def extract_title(self, item):
#         for atom in item['mainState']:
#             if atom['id'] == 'name':
#                 self.book_info['title'] = atom['atom']['textAtom']['text'].split('|')[0].strip()
#
#     def parse_book_info(self):
#         product_parsed_name = self.parse_product_for_query()
#         product_url = self.get_product_url(product_parsed_name)
#         self.browser.get(product_url)
#         content = self.browser.find_element(By.ID, 'json').text
#         data = json.loads(content)
#         for key, value in data['widgetStates'].items():
#             if 'webCharacteristics' in key:
#                 self.characteristics = json.loads(value)['characteristics'][0]['short']
#             if 'richAnnotation' in value:
#                 self.book_info['annotation'] = self.remove_html_tags(json.loads(value)['richAnnotation'])
#
#     def extract_fields(self):
#         self.parse_book_info()
#         book_fields = dict()
#         for value in self.characteristics:
#             if value['key'] in self.fields_for_parse.keys():
#                 book_fields.update({self.fields_for_parse[value['key']]: value["values"][0]["text"]})
#         self.book_info.update(book_fields)
#         if not self.search_request.replace(' ', '').isalnum():
#             self.book_info = {key: self.book_info[key] for key in ['title', 'annotation', 'author']}
#
#     @staticmethod
#     def remove_html_tags(text):
#         import re
#         clean = re.compile('<.*?>')
#         return re.sub(clean, '', text)
#
#
# if __name__ == '__main__':
#

#
#     # local configuration
#     options = Options()
#     options.headless = True
#     browser = webdriver.Firefox(options=options)
#
#     # server configuration
#     # options = webdriver.ChromeOptions()
#     # options.headless = True
#     # options.add_argument("--no-sandbox")
#     # browser = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))
#
#     ParseManager.register('get_request_collector')
#     ParseManager.register('get_output_collector')
#
#     reader_manager = ParseManager(address=('127.0.0.1', 1191), authkey=b'qwerasdf')
#     reader_manager.connect()
#
#     request_collector = reader_manager.get_request_collector()
#     output_collector = reader_manager.get_output_collector()
#
#
#     def process_request(key, parsed_content):
#         output_collector.update({key: parsed_content})
#
#
#     while True:
#         if request_collector.values():
#             request = request_collector.popitem()
#             parser = OzonSeleniumForeverParser(request[1], browser)
#
#             try:
#                 parser.extract_fields()
#                 process_request(request[0], parser.book_info)
#             except Exception as e:
#                 process_request(request[0], None)
#                 print(e)
#         sleep(1)
#         print(f'request_collector: {request_collector}')
#         pprint(f'output_collector: {output_collector}')
