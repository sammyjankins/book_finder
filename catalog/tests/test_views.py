from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from catalog.models import BookCase, Shelf, Book, Author, Note


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


class TestView(TestCase):

    def setUp(self):
        self.client = Client()

        self.test_user = User.objects.create_user(username='testuser', password='pass')
        self.test_user.save()
        self.test_user2 = User.objects.create_user(username='testuser2', password='pass')
        self.test_user2.save()
        self.client.login(username='testuser', password='pass')


class TestBookcaseListView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestBookcaseListView, self).setUp()

        for case_num in range(13):
            BookCase.objects.create(title=f'bookcase{case_num}', shelf_count=1, section_count=1, row_count=1,
                                    owner=self.test_user)

        for case_num in range(5):
            BookCase.objects.create(title=f'bookcase{case_num}', shelf_count=1, section_count=1, row_count=1,
                                    owner=self.test_user2)

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


class TestAuthorListView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestAuthorListView, self).setUp()
        BookCase.objects.create(title='bookcase', shelf_count=1, section_count=1, row_count=1,
                                owner=self.test_user)
        for case_num in range(13):
            Author.objects.create(name=f'author{case_num}', date_of_birth='04.08.1516', country='Westeros',
                                  owner=self.test_user)

        for case_num in range(5):
            Author.objects.create(name=f'author{case_num}', date_of_birth='04.08.1516', country='Westeros',
                                  owner=self.test_user2)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/author/all/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('author-list'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('author-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/author_list.html')

    def test_amount_of_objects_on_page(self):
        response = self.client.get(reverse('author-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertEqual(response.context['is_paginated'], True)
        self.assertEqual(len(response.context['object_list']), 10)
        response = self.client.get(reverse('author-list') + '?page=2')
        self.assertTrue(len(response.context['object_list']) == 3)

    def test_only_owners_objects_visible(self):
        self.client.logout()
        self.client.login(username='testuser2', password='pass')
        response = self.client.get(reverse('author-list'))
        self.assertEqual(len(response.context['object_list']), 5)
        for author in response.context['object_list']:
            self.assertEqual(author.owner.username, 'testuser2')


class TestBookListView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestBookListView, self).setUp()
        BookCase.objects.create(title='bookcase', shelf_count=1, section_count=1, row_count=1,
                                owner=self.test_user)
        shelf = Shelf.objects.last()
        author = Author.objects.create(name='John Fowles', owner=self.test_user)

        for case_num in range(5):
            Book.objects.create(title=f'book{case_num}', pages=100, year_of_publication=f'20{case_num}',
                                language='EN', ISBN=f'978-0-{case_num}-947835-5', type_of_cover='обложка',
                                read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                                shelf=shelf, author=author, favorite=False, owner=self.test_user)
        for case_num in range(5):
            Book.objects.create(title=f'book{case_num}', pages=100, year_of_publication=f'20{case_num}',
                                language='EN', ISBN=f'978-0-{case_num}-947835-5', type_of_cover='обложка',
                                read=True, annotation='On a remote Greek island, Nicholas Urfe ...',
                                shelf=shelf, author=author, favorite=False, owner=self.test_user)
        for case_num in range(5):
            Book.objects.create(title=f'book{case_num}', pages=100, year_of_publication=f'20{case_num}',
                                language='EN', ISBN=f'978-0-{case_num}-947835-5', type_of_cover='обложка',
                                read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                                shelf=shelf, author=author, favorite=True, owner=self.test_user)

        BookCase.objects.create(title='bookcase', shelf_count=1, section_count=1, row_count=1,
                                owner=self.test_user2)
        shelf2 = Shelf.objects.last()
        author2 = Author.objects.create(name='John Fowles', owner=self.test_user2)

        for case_num in range(5):
            Book.objects.create(title=f'book{case_num}', pages=100, year_of_publication=f'20{case_num}',
                                language='EN', ISBN=f'978-0-{case_num}-947835-5', type_of_cover='обложка',
                                read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                                shelf=shelf2, author=author2, favorite=False, owner=self.test_user2)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/book/all/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('book-list'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('book-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/book_list.html')

    def test_amount_of_objects_on_page(self):
        response = self.client.get(reverse('book-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertEqual(response.context['is_paginated'], True)
        self.assertEqual(len(response.context['object_list']), 10)
        response = self.client.get(reverse('book-list') + '?page=2')
        self.assertTrue(len(response.context['object_list']) == 5)

    def test_only_owners_objects_visible(self):
        self.client.logout()
        self.client.login(username='testuser2', password='pass')
        response = self.client.get(reverse('book-list'))
        self.assertEqual(len(response.context['object_list']), 5)
        for book in response.context['object_list']:
            self.assertEqual(book.owner.username, 'testuser2')

    def test_favorite_books(self):
        response = self.client.get(reverse('favorite-list'))
        self.assertEqual(len(response.context['object_list']), 5)
        for book in response.context['object_list']:
            self.assertEqual(book.favorite, True)

    def test_read_books(self):
        response = self.client.get(reverse('read-list'))
        self.assertEqual(len(response.context['object_list']), 5)
        for book in response.context['object_list']:
            self.assertEqual(book.read, True)

    def test_unread_books(self):
        response = self.client.get(reverse('unread-list'))
        self.assertEqual(len(response.context['object_list']), 10)
        for book in response.context['object_list']:
            self.assertEqual(book.read, False)


class TestSearchListView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestSearchListView, self).setUp()
        BookCase.objects.create(title='bookcase', shelf_count=1, section_count=1, row_count=1,
                                owner=self.test_user)
        shelf = Shelf.objects.last()
        s_king = Author.objects.create(name='Stephen King', country='X', date_of_birth='01.01.1900',
                                       owner=self.test_user)
        t_king = Author.objects.create(name='Tabitha King', country='X', date_of_birth='01.01.1900',
                                       owner=self.test_user)
        j_fowles = Author.objects.create(name='John Fowles', country='X', date_of_birth='01.01.1900',
                                         owner=self.test_user)

        Book.objects.bulk_create([
            Book(title='It', pages=100, year_of_publication='2000',
                 language='EN', ISBN='978-0-947835-5111', type_of_cover='обложка',
                 read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                 shelf=shelf, author=s_king, favorite=True, owner=self.test_user),
            Book(title='Random book about king', pages=100, year_of_publication='2000',
                 language='EN', ISBN='978-0-947835-5111', type_of_cover='обложка',
                 read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                 shelf=shelf, author=j_fowles, favorite=True, owner=self.test_user),
            Book(title='Small World', pages=100, year_of_publication='2000',
                 language='EN', ISBN='978-0-947835-5111', type_of_cover='обложка',
                 read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                 shelf=shelf, author=t_king, favorite=True, owner=self.test_user),
        ])

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/search/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('search-list'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('search-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/search_list.html')

    def test_found_right_objects(self):
        response = self.client.get('/search/', {'q': "king", })
        self.assertEqual(len(response.context['object_list']['author']), 2)
        self.assertEqual(len(response.context['object_list']['book']), 1)


class TestBookcaseDetailView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestBookcaseDetailView, self).setUp()
        self.bookcase = BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                                owner=self.test_user)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/bookcase/{self.bookcase.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('bookcase-detail', kwargs={'pk': self.bookcase.pk}))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('bookcase-detail', kwargs={'pk': self.bookcase.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/bookcase_detail.html')

    def test_object_unavailable_for_other_user(self):
        self.client.logout()
        self.client.login(username='testuser2', password='pass')
        response = self.client.get(reverse('bookcase-detail', kwargs={'pk': self.bookcase.pk}))
        self.assertEqual(response.status_code, 403)


class TestShelfDetailView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestShelfDetailView, self).setUp()
        self.bookcase = BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                                owner=self.test_user)
        self.shelf = Shelf.objects.last()

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/shelf/{self.shelf.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('shelf-detail', kwargs={'pk': self.shelf.pk}))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('shelf-detail', kwargs={'pk': self.shelf.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/shelf_detail.html')

    def test_object_unavailable_for_other_user(self):
        self.client.logout()
        self.client.login(username='testuser2', password='pass')
        response = self.client.get(reverse('shelf-detail', kwargs={'pk': self.shelf.pk}))
        self.assertEqual(response.status_code, 403)


class TestAuthorDetailView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestAuthorDetailView, self).setUp()
        BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                owner=self.test_user)
        self.author = Author.objects.create(name='author-test', date_of_birth='04.08.1516', country='Westeros',
                                            owner=self.test_user)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/author/{self.author.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('author-detail', kwargs={'pk': self.author.pk}))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('author-detail', kwargs={'pk': self.author.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/author_detail.html')

    def test_object_unavailable_for_other_user(self):
        self.client.logout()
        self.client.login(username='testuser2', password='pass')
        response = self.client.get(reverse('author-detail', kwargs={'pk': self.author.pk}))
        self.assertEqual(response.status_code, 403)


class TestBookDetailView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestBookDetailView, self).setUp()
        BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                owner=self.test_user)
        author = Author.objects.create(name='author-test', date_of_birth='04.08.1516', country='Westeros',
                                       owner=self.test_user)
        shelf = Shelf.objects.last()
        self.book = Book.objects.create(title='It', pages=100, year_of_publication='2000',
                                        language='EN', ISBN='978-0-947835-5111', type_of_cover='обложка',
                                        read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                                        shelf=shelf, author=author, favorite=True, owner=self.test_user)

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/book/{self.book.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/book_detail.html')

    def test_object_unavailable_for_other_user(self):
        self.client.logout()
        self.client.login(username='testuser2', password='pass')
        response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.pk}))
        self.assertEqual(response.status_code, 403)


class TestBookCaseCreateView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestBookCaseCreateView, self).setUp()

    def test_created_bookcase_and_owner_set(self):
        self.client.post('/bookcase/new/', {'title': "bookcase_test", 'shelf_count': 2,
                                            'section_count': 2, 'row_count': 2})
        self.assertEqual(BookCase.objects.last().title, "bookcase_test")
        self.assertEqual(BookCase.objects.last().owner, self.test_user)
        self.assertEqual(BookCase.objects.last().shelves.count(), 8)

    def test_display_bookcase(self):
        bookcase = BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                           owner=self.test_user)
        response = self.client.get(reverse('bookcase-detail', kwargs={'pk': bookcase.pk}))
        self.assertContains(response, "bookcase_test")


class TestAuthorCreateView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestAuthorCreateView, self).setUp()
        BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                owner=self.test_user)

    def test_created_author_and_owner_set(self):
        self.client.post('/author/new/', {'name': "author_test", 'date_of_birth': '04.08.1516',
                                          'country': 'Westeros'})
        self.assertEqual(Author.objects.last().name, "author_test")
        self.assertEqual(Author.objects.last().owner, self.test_user)

    def test_display_author(self):
        author = Author.objects.create(name='author_test', date_of_birth='04.08.1516', country='Westeros',
                                       owner=self.test_user)
        response = self.client.get(reverse('author-detail', kwargs={'pk': author.pk}))
        self.assertContains(response, "author_test")


class TestBookCreateView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestBookCreateView, self).setUp()
        BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                owner=self.test_user)
        self.shelf = Shelf.objects.last()

    def test_created_book_and_owner_set(self):
        self.client.post('/book/new/', {'title': "book_test", 'new_author': 'author_test', 'shelf': self.shelf.pk,
                                        'pages': ''})
        self.assertEqual(Book.objects.last().title, "book_test")
        self.assertEqual(Book.objects.last().owner, self.test_user)
        self.assertEqual(Author.objects.last().name, 'author_test')

    def test_display_book(self):
        author = Author.objects.create(name='author_test', date_of_birth='04.08.1516', country='Westeros',
                                       owner=self.test_user)
        book = Book.objects.create(title='book_test', pages=100, year_of_publication='2000',
                                   language='EN', ISBN='978-0-947835-5111', type_of_cover='обложка',
                                   read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                                   shelf=self.shelf, author=author, favorite=True, owner=self.test_user)
        response = self.client.get(reverse('book-detail', kwargs={'pk': book.pk}))
        self.assertContains(response, "book_test")


class TestNoteCreateView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestNoteCreateView, self).setUp()
        BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                owner=self.test_user)
        shelf = Shelf.objects.last()
        author = Author.objects.create(name='author_test', date_of_birth='04.08.1516', country='Westeros',
                                       owner=self.test_user)
        self.book = Book.objects.create(title='book_test', pages=100, year_of_publication='2000',
                                        language='EN', ISBN='978-0-947835-5111', type_of_cover='обложка',
                                        read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                                        shelf=shelf, author=author, favorite=True, owner=self.test_user)

    def test_created_note_and_owner_set(self):
        self.client.post(f'/book/{self.book.pk}/note/', {'text': "note test text", 'book': self.book.pk})
        self.assertEqual(Note.objects.last().owner, self.test_user)
        self.assertEqual(Note.objects.last().text, "note test text")

    def test_display_note(self):
        Note.objects.create(text="note test text", book=self.book, owner=self.test_user)
        response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.pk}))
        self.assertContains(response, "note test text")


class TestBookCaseUpdateView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestBookCaseUpdateView, self).setUp()
        self.bookcase = BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                                owner=self.test_user)

    def test_bookcase_updated(self):
        response = self.client.post(reverse('bookcase-update', kwargs={'pk': self.bookcase.pk}),
                                    {'title': 'changed title'})
        self.assertEqual(response.status_code, 302)
        self.bookcase.refresh_from_db()
        self.assertEqual(self.bookcase.title, "changed title")


class TestShelfUpdateView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestShelfUpdateView, self).setUp()
        self.bookcase = BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                                owner=self.test_user)
        self.shelf = Shelf.objects.last()

    def test_shelf_updated(self):
        self.assertEqual(self.shelf.title, "Вторая полка")
        response = self.client.post(reverse('shelf-update', kwargs={'pk': self.shelf.pk}),
                                    {'title': 'changed title'})
        self.assertEqual(response.status_code, 302)
        self.shelf.refresh_from_db()
        self.assertEqual(self.shelf.title, "changed title")


class TestAuthorUpdateView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestAuthorUpdateView, self).setUp()
        self.bookcase = BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                                owner=self.test_user)
        self.author = Author.objects.create(name='author_test', date_of_birth='04.08.1516', country='Westeros',
                                            owner=self.test_user)

    def test_author_updated(self):
        response = self.client.post(reverse('author-update', kwargs={'pk': self.author.pk}),
                                    {'name': 'changed name', 'date_of_birth': '01.01.1900', 'country': 'EN'})
        self.assertEqual(response.status_code, 302)
        self.author.refresh_from_db()
        self.assertEqual(self.author.name, "changed name")
        self.assertEqual(self.author.date_of_birth, "01.01.1900")
        self.assertEqual(self.author.country, "EN")


class TestBookUpdateView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestBookUpdateView, self).setUp()
        BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                owner=self.test_user)
        shelf = Shelf.objects.last()
        author = Author.objects.create(name='author_test', date_of_birth='04.08.1516', country='Westeros',
                                       owner=self.test_user)
        self.book = Book.objects.create(title='book_test', pages=100, year_of_publication='2000',
                                        language='EN', ISBN='978-0-947835-5111', type_of_cover='обложка',
                                        read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                                        shelf=shelf, author=author, favorite=True, owner=self.test_user)

    def test_book_updated(self):
        new_shelf = Shelf.objects.first()
        response = self.client.post(reverse('book-update', kwargs={'pk': self.book.pk}),
                                    {'title': 'changed title', 'pages': 200, 'year_of_publication': '1950',
                                     'language': 'changed', 'ISBN': '1234567891231', 'type_of_cover': 'changed cover',
                                     'annotation': 'changed annotation', 'shelf': new_shelf.pk,
                                     'new_author': 'changed author'})
        self.assertEqual(response.status_code, 302)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "changed title")
        self.assertEqual(self.book.pages, 200)
        self.assertEqual(self.book.year_of_publication, '1950')
        self.assertEqual(self.book.language, 'changed')
        self.assertEqual(self.book.ISBN, '1234567891231')
        self.assertEqual(self.book.type_of_cover, 'changed cover')
        self.assertEqual(self.book.annotation, 'changed annotation')
        self.assertEqual(self.book.shelf, new_shelf)
        self.assertEqual(self.book.author.name, 'changed author')


class TestNoteUpdateView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestNoteUpdateView, self).setUp()
        BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                owner=self.test_user)
        shelf = Shelf.objects.last()
        author = Author.objects.create(name='author_test', date_of_birth='04.08.1516', country='Westeros',
                                       owner=self.test_user)
        book = Book.objects.create(title='book_test', pages=100, year_of_publication='2000',
                                   language='EN', ISBN='978-0-947835-5111', type_of_cover='обложка',
                                   read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                                   shelf=shelf, author=author, favorite=True, owner=self.test_user)
        self.note = Note.objects.create(text="note test text", book=book, owner=self.test_user)

    def test_note_updated(self):
        response = self.client.post(reverse('note-update', kwargs={'pk': self.note.pk}),
                                    {'text': 'changed text', })
        self.assertEqual(response.status_code, 302)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, "changed text")


class TestBookCaseDeleteView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestBookCaseDeleteView, self).setUp()
        self.bookcase = BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                                owner=self.test_user)
        shelf = Shelf.objects.last()
        author = Author.objects.create(name='author_test', date_of_birth='04.08.1516', country='Westeros',
                                       owner=self.test_user)
        Book.objects.create(title='book_test', pages=100, year_of_publication='2000',
                            language='EN', ISBN='978-0-947835-5111', type_of_cover='обложка',
                            read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                            shelf=shelf, author=author, favorite=True, owner=self.test_user)

    def test_delete_bookcase_get_request(self):
        response = self.client.get(reverse('bookcase-delete', kwargs={'pk': self.bookcase.pk}), follow=True)
        self.assertContains(response, 'Шкаф будет удален включая его содержимое. Вы уверены, что хотите удалить шкаф')

    def test_delete_bookcase_post_request(self):
        self.assertEqual(Shelf.objects.count(), 4)
        self.assertEqual(Book.objects.count(), 1)
        response = self.client.post(reverse('bookcase-delete', kwargs={'pk': self.bookcase.pk}), follow=True)
        self.assertRedirects(response, reverse('bookcase-list'), status_code=302)
        self.assertEqual(BookCase.objects.count(), 0)
        self.assertEqual(Shelf.objects.count(), 0)
        self.assertEqual(Book.objects.count(), 0)


class TestAuthorDeleteView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestAuthorDeleteView, self).setUp()
        BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                owner=self.test_user)
        shelf = Shelf.objects.last()
        self.author = Author.objects.create(name='author_test', date_of_birth='04.08.1516', country='Westeros',
                                            owner=self.test_user)
        Book.objects.create(title='book_test', pages=100, year_of_publication='2000',
                            language='EN', ISBN='978-0-947835-5111', type_of_cover='обложка',
                            read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                            shelf=shelf, author=self.author, favorite=True, owner=self.test_user)

    def test_delete_author_get_request(self):
        response = self.client.get(reverse('author-delete', kwargs={'pk': self.author.pk}), follow=True)
        self.assertContains(response, 'Вместе с автором будут удалены его книги. Вы уверены, что хотите удалить автора')

    def test_delete_author_post_request(self):
        self.assertEqual(Book.objects.count(), 1)
        response = self.client.post(reverse('author-delete', kwargs={'pk': self.author.pk}), follow=True)
        self.assertRedirects(response, reverse('author-list'), status_code=302)
        self.assertEqual(Author.objects.count(), 0)
        self.assertEqual(Book.objects.count(), 0)


class TestBookDeleteView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestBookDeleteView, self).setUp()
        BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                owner=self.test_user)
        shelf = Shelf.objects.last()
        author = Author.objects.create(name='author_test', date_of_birth='04.08.1516', country='Westeros',
                                       owner=self.test_user)
        self.book = Book.objects.create(title='book_test', pages=100, year_of_publication='2000',
                                        language='EN', ISBN='978-0-947835-5111', type_of_cover='обложка',
                                        read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                                        shelf=shelf, author=author, favorite=True, owner=self.test_user)
        Note.objects.create(text="note test text", book=self.book, owner=self.test_user)

    def test_delete_book_get_request(self):
        response = self.client.get(reverse('book-delete', kwargs={'pk': self.book.pk}), follow=True)
        self.assertContains(response, 'Вы уверены, что хотите удалить книгу')

    def test_delete_book_post_request(self):
        self.assertEqual(Note.objects.count(), 1)
        response = self.client.post(reverse('book-delete', kwargs={'pk': self.book.pk}), follow=True)
        self.assertRedirects(response, reverse('book-list'), status_code=302)
        self.assertEqual(Book.objects.count(), 0)
        self.assertEqual(Note.objects.count(), 0)


class TestSwapBookStates(TestView):

    def setUp(self, *args, **kwargs):
        super(TestSwapBookStates, self).setUp()
        BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                owner=self.test_user)
        shelf = Shelf.objects.last()
        author = Author.objects.create(name='author_test', date_of_birth='04.08.1516', country='Westeros',
                                       owner=self.test_user)
        self.book = Book.objects.create(title='book_test', pages=100, year_of_publication='2000',
                                        language='EN', ISBN='978-0-947835-5111', type_of_cover='обложка',
                                        read=False, annotation='On a remote Greek island, Nicholas Urfe ...',
                                        shelf=shelf, author=author, favorite=False, owner=self.test_user)

    def test_swap_favorite_post_request(self):
        self.assertFalse(self.book.favorite)
        response = self.client.post(reverse('swap-favorite', kwargs={'pk': self.book.pk}), follow=True)
        self.assertRedirects(response, reverse('book-detail', kwargs={'pk': self.book.pk}), status_code=302)
        self.book.refresh_from_db()
        self.assertTrue(self.book.favorite)

    def test_swap_read_post_request(self):
        self.assertFalse(self.book.read)
        response = self.client.post(reverse('swap-read', kwargs={'pk': self.book.pk}), follow=True)
        self.assertRedirects(response, reverse('book-detail', kwargs={'pk': self.book.pk}), status_code=302)
        self.book.refresh_from_db()
        self.assertTrue(self.book.read)


class TestNewActiveShelfView(TestView):

    def setUp(self, *args, **kwargs):
        super(TestNewActiveShelfView, self).setUp()
        BookCase.objects.create(title='bookcase_test', shelf_count=2, section_count=1, row_count=2,
                                owner=self.test_user)
        self.active_shelf = Shelf.objects.last()
        self.inactive_shelf = Shelf.objects.first()

    def test_new_active_shelf_post_request(self):
        self.assertTrue(self.active_shelf.is_current)
        self.assertFalse(self.inactive_shelf.is_current)
        response = self.client.post(reverse('new-active-shelf', kwargs={'pk': self.inactive_shelf.pk}), follow=True)
        self.assertRedirects(response, reverse('shelf-detail', kwargs={'pk': self.inactive_shelf.pk}), status_code=302)
        self.active_shelf.refresh_from_db()
        self.inactive_shelf.refresh_from_db()
        self.assertFalse(self.active_shelf.is_current)
        self.assertTrue(self.inactive_shelf.is_current)
