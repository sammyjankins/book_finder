from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from catalog.models import BookCase, Shelf, Book, Author, Note
import json


class TestAuthorization(TestCase):

    def setUp(self):
        self.client = Client()

        test_user = User.objects.create_user(username='testuser', password='pass')
        test_user.save()

    def test_login(self):
        response = self.client.get(reverse('bookcase-list'))
        self.assertEqual(response.status_code, 302)

        self.client.login(username='testuser', password='pass')

        response = self.client.get(reverse('bookcase-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/home.html')
        self.assertTemplateUsed(response, 'catalog/base.html')


class TestBookcaseListView(TestCase):

    def setUp(self):
        self.client = Client()

        test_user = User.objects.create_user(username='testuser', password='pass')
        test_user.save()
        test_user2 = User.objects.create_user(username='testuser2', password='pass')
        test_user2.save()
        self.client.login(username='testuser', password='pass')

        for case_num in range(13):
            BookCase.objects.create(title=f'bookcase{case_num}', shelf_count=1, section_count=1, row_count=1,
                                    owner=test_user)

        for case_num in range(5):
            BookCase.objects.create(title=f'bookcase{case_num}', shelf_count=1, section_count=1, row_count=1,
                                    owner=test_user2)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('bookcase-list'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('bookcase-list'))
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'catalog/home.html')

    def test_amount_of_objects_on_page(self):
        response = self.client.get(reverse('bookcase-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertEqual(response.context['is_paginated'], True)
        self.assertEqual(len(response.context['object_list']), 10)
        response = self.client.get(reverse('bookcase-list') + '?page=2')
        self.assertTrue(len(response.context['object_list']) == 3)

    def test_only_owners_objects_visible(self):
        self.client.logout()
        self.client.login(username='testuser2', password='pass')
        response = self.client.get(reverse('bookcase-list'))
        self.assertEqual(len(response.context['object_list']), 5)
        for bookcase in response.context['object_list']:
            self.assertEqual(bookcase.owner.username, 'testuser2')


class TestAuthorListView(TestCase):

    def setUp(self):
        self.client = Client()

        test_user = User.objects.create_user(username='testuser', password='pass')
        test_user.save()
        test_user2 = User.objects.create_user(username='testuser2', password='pass')
        test_user2.save()
        self.client.login(username='testuser', password='pass')

        for case_num in range(13):
            Author.objects.create(name=f'author{case_num}', date_of_birth='04.08.1516', country='Westeros',
                                  owner=test_user)

        for case_num in range(5):
            Author.objects.create(name=f'author{case_num}', date_of_birth='04.08.1516', country='Westeros',
                                  owner=test_user2)

    def test_redirect_without_bookcases(self):
        response = self.client.get(reverse('author-list'))
        self.assertEqual(response.status_code, 302)
