from selenium import webdriver
import unittest


class NewVisitorTest(unittest.TestCase):
    """тест нового посетителя"""

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_visit_homepage(self):
        # пользователь посещает домашнюю страницу веб-сайта

        self.browser.get('http://localhost:8000')
        # оценка заголовка сайта

        # содержимое главной страницы
        self.assertIn('Каталог', self.browser.title)
        header_text = self.browser.find_element(by='tag name', value='h1').text
        self.assertIn('Ваша библиотека', header_text)

        # на странице список книжных шкафов
        bookcases = self.browser.find_element(by='id', value='bookcases')
        self.assertIn('list-group', bookcases.get_attribute('class'))

        # и предложение создать новый шкаф
        add_button = self.browser.find_element(by='id', value='add-bookcase')
        self.assertEqual(add_button.tag_name, 'a')
        self.assertEqual(add_button.text, 'Добавить новый книжный шкаф')

        # self.fail('Завершить тест')


if __name__ == '__main__':
    unittest.main(warnings='ignore')
