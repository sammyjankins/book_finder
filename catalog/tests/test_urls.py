from django.test import SimpleTestCase
from django.urls import reverse, resolve
# from catalog.views import bookcase_list_view


# class TestUrls(SimpleTestCase):
#     """
#         function view testing:
#
#         def test_home_url_is_resolved(self):
#             url = reverse('catalog-home')
#             self.assertEqual(resolve(url).func, home)
#
#         class view testing:
#
#         def test_home_url_is_resolved(self):
#             url = reverse('catalog-home')
#             self.assertEqual(resolve(url).func.view_class, HomeView)
#
#         parameter view testing:
#
#         def test_home_url_is_resolved(self):
#             url = reverse('catalog-home', args=['some-id'])
#             self.assertEqual(resolve(url).func, home)
#
#     """
#
#     def test_home_url_is_resolved(self):
#         url = reverse('bookcase-list')
#         self.assertEqual(resolve(url).func, bookcase_list_view)
