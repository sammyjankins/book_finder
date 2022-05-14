from django.test import TestCase, Client
from django.urls import reverse


class TestViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')

    def test_register_view_GET(self):
        response = self.client.get(self.register_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
        self.assertTemplateUsed(response, 'catalog/base.html')

    def test_register_view_POST_reacts_to_short_pass(self):
        response = self.client.post(self.register_url, {
            'username': ['testuser'],
            'password1': ['some'],
            'password2': ['some'],
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
        self.assertContains(response, 'This password is too short. It must contain at least 8 characters.')

    def test_register_view_POST_reacts_to_pass_mismatch(self):
        response = self.client.post(self.register_url, {
            'username': 'testuser',
            'password1': 'some',
            'password2': 'pass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
        self.assertContains(response, 'The two password fields didn’t match.')

    def _get_token(self, url, data):
        resp = self.client.get(url)
        data['csrfmiddlewaretoken'] = resp.cookies['csrftoken'].value
        return data
