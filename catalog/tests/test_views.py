from django.test import TestCase, Client
from django.urls import reverse
from catalog.models import BookCase
import json


class TestViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.bookcase_list_url = reverse('bookcase-list')

    def test_bookcase_list_GET(self):
        response = self.client.get(self.bookcase_list_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/home.html')
        self.assertTemplateUsed(response, 'catalog/base.html')
