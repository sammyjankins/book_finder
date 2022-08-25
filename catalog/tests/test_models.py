from unittest.mock import Mock

from django.contrib.auth.models import User
from django.test import TestCase

from catalog.models import Author, BookCase, Shelf, Book, Note


class BookCaseTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(username='username', password='12345')
        cls.bookcase = BookCase.objects.create(title='Sci-Fi', shelf_count=2, section_count=2, row_count=2, owner=user)

    def test_title_label(self):
        field_label = self.bookcase._meta.get_field('title').verbose_name
        self.assertEquals(field_label, 'Название')

    def test_shelf_count_label(self):
        field_label = self.bookcase._meta.get_field('shelf_count').verbose_name
        self.assertEquals(field_label, 'Количество полок')

    def test_section_count_label(self):
        field_label = self.bookcase._meta.get_field('section_count').verbose_name
        self.assertEquals(field_label, 'Количество секций')

    def test_row_count_label(self):
        field_label = self.bookcase._meta.get_field('row_count').verbose_name
        self.assertEquals(field_label, 'Количество рядов')

    def test_title_max_length(self):
        max_length = self.bookcase._meta.get_field('title').max_length
        self.assertEquals(max_length, 100)

    def test_created_shelves(self):
        shelves = Shelf.objects.filter(bookcase=self.bookcase)
        expected_count = self.bookcase.shelf_count * self.bookcase.section_count * self.bookcase.row_count
        self.assertEquals(expected_count, shelves.count())

    def test_get_absolute_url(self):
        self.assertEquals(self.bookcase.get_absolute_url(), f'/bookcase/{self.bookcase.pk}/')

    def test_str_method(self):
        self.assertEquals(str(self.bookcase), self.bookcase.title)


class ShelfTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(username='username', password='12345')
        BookCase.objects.create(title='Sci-Fi', shelf_count=2, section_count=2, row_count=2, owner=user)
        cls.shelf = Shelf.objects.last()

    def test_title_label(self):
        field_label = self.shelf._meta.get_field('title').verbose_name
        self.assertEquals(field_label, 'Название')

    def test_title_max_length(self):
        max_length = self.shelf._meta.get_field('title').max_length
        self.assertEquals(max_length, 100)

    def test_row_max_length(self):
        max_length = self.shelf._meta.get_field('row').max_length
        self.assertEquals(max_length, 100)

    def test_autogenerated_title(self):
        self.assertEquals(self.shelf.title, 'Вторая полка справа')

    def test_autogenerated_row(self):
        self.assertEquals(self.shelf.row, 'Второй')

    def test_get_current_shelf(self):
        not_current = Shelf.objects.first()
        current = not_current.get_current_shelf()
        self.assertEquals(current.is_current, True)

    def test_current_is_last_created(self):
        not_current = Shelf.objects.first()
        current_shelf = not_current.get_current_shelf()
        self.assertEquals(self.shelf, current_shelf)

    def test_the_only_current_shelf(self):
        current = 0
        shelves = Shelf.objects.all()
        for shelf in shelves:
            if shelf.is_current:
                current += 1
        self.assertEquals(current, 1)

    def test_str_method(self):
        self.assertEquals(str(self.shelf), f'{self.shelf.title.lower()}, {self.shelf.row.lower()} ряд')


class AuthorModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(username='username', password='12345')
        cls.author = Author.objects.create(name='Carl Sagan', date_of_birth='09.11.1934', country='USA', owner=user)

    def test_name_label(self):
        field_label = self.author._meta.get_field('name').verbose_name
        self.assertEquals(field_label, 'Имя')

    def test_date_of_birth_label(self):
        field_label = self.author._meta.get_field('date_of_birth').verbose_name
        self.assertEquals(field_label, 'Дата рождения')

    def test_country_label(self):
        field_label = self.author._meta.get_field('country').verbose_name
        self.assertEquals(field_label, 'Страна')

    def test_name_max_length(self):
        max_length = self.author._meta.get_field('name').max_length
        self.assertEquals(max_length, 150)

    def test_date_of_birth_length(self):
        max_length = self.author._meta.get_field('date_of_birth').max_length
        self.assertEquals(max_length, 15)

    def test_country_length(self):
        max_length = self.author._meta.get_field('country').max_length
        self.assertEquals(max_length, 100)

    def test_str_method(self):
        self.assertEquals(str(self.author), self.author.name)

    def test_get_absolute_url(self):
        self.assertEquals(self.author.get_absolute_url(), f'/author/{self.author.pk}/')

    def test_model_verbose_name(self):
        self.assertEqual(Author._meta.verbose_name, 'Автор')


class BookModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(username='username', password='12345')
        BookCase.objects.create(title='Bedroom bookcase', shelf_count=2, section_count=2, row_count=2,
                                owner=user)
        shelf = Shelf.objects.last()
        author = Author.objects.filter(name='John Fowles', owner=user).first()
        if author is None:
            author = Author.objects.create(name='John Fowles', owner=user)
        cls.book = Book.objects.create(title='The Magus', pages='666', year_of_publication='2016', language='EN',
                                       ISBN='978-0-09-947835-5', type_of_cover='мягкая обложка', read=False,
                                       annotation='On a remote Greek island, Nicholas Urfe finds himself embroiled '
                                                  'in the deceptions of a master trickster. Fowles unfolds a tale '
                                                  'that is lush with over-powering imagery in a spellbinding '
                                                  'exploration of the complexities of the human mind.',
                                       shelf=shelf, author=author, favorite=False, owner=user)

    def test_title_label(self):
        field_label = self.book._meta.get_field('title').verbose_name
        self.assertEquals(field_label, 'Название')

    def test_pages_label(self):
        field_label = self.book._meta.get_field('pages').verbose_name
        self.assertEquals(field_label, 'Количество страниц')

    def test_year_of_publication_label(self):
        field_label = self.book._meta.get_field('year_of_publication').verbose_name
        self.assertEquals(field_label, 'Год издания')

    def test_language_label(self):
        field_label = self.book._meta.get_field('language').verbose_name
        self.assertEquals(field_label, 'Язык')

    def test_ISBN_label(self):
        field_label = self.book._meta.get_field('ISBN').verbose_name
        self.assertEquals(field_label, 'ISBN')

    def test_type_of_cover_label(self):
        field_label = self.book._meta.get_field('type_of_cover').verbose_name
        self.assertEquals(field_label, 'Тип обложки')

    def test_read_label(self):
        field_label = self.book._meta.get_field('read').verbose_name
        self.assertEquals(field_label, 'Прочитана')

    def test_annotation_label(self):
        field_label = self.book._meta.get_field('annotation').verbose_name
        self.assertEquals(field_label, 'Аннотация')

    def test_shelf_label(self):
        field_label = self.book._meta.get_field('shelf').verbose_name
        self.assertEquals(field_label, 'Полка')

    def test_author_label(self):
        field_label = self.book._meta.get_field('author').verbose_name
        self.assertEquals(field_label, 'Автор')

    def test_new_author_label(self):
        field_label = self.book._meta.get_field('new_author').verbose_name
        self.assertEquals(field_label, 'Новый автор')

    def test_favorite_label(self):
        field_label = self.book._meta.get_field('favorite').verbose_name
        self.assertEquals(field_label, 'Избранное')

    def test_title_max_length(self):
        max_length = self.book._meta.get_field('title').max_length
        self.assertEquals(max_length, 150)

    def test_year_of_publication_max_length(self):
        max_length = self.book._meta.get_field('year_of_publication').max_length
        self.assertEquals(max_length, 10)

    def test_language_max_length(self):
        max_length = self.book._meta.get_field('language').max_length
        self.assertEquals(max_length, 50)

    def test_ISBN_max_length(self):
        max_length = self.book._meta.get_field('ISBN').max_length
        self.assertEquals(max_length, 100)

    def test_type_of_cover_max_length(self):
        max_length = self.book._meta.get_field('type_of_cover').max_length
        self.assertEquals(max_length, 25)

    def test_new_author_max_length(self):
        max_length = self.book._meta.get_field('new_author').max_length
        self.assertEquals(max_length, 150)

    def test_str_method(self):
        self.assertEquals(str(self.book), self.book.title)

    def test_get_absolute_url(self):
        self.assertEquals(self.book.get_absolute_url(), f'/book/{self.book.pk}/')


class NoteModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(username='username', password='12345')
        BookCase.objects.create(title='Random bookcase', shelf_count=1, section_count=1, row_count=1,
                                owner=user)
        shelf = Shelf.objects.first()
        author = Author.objects.filter(name='John Smith', owner=user).first()
        if author is None:
            author = Author.objects.create(name='John Smith', owner=user)
        cls.book = Book.objects.create(title='The Ipsum', shelf=shelf, author=author, favorite=False, owner=user)
        cls.note = Note.objects.create(text='Bonbon marshmallow gummi bears icing tart marshmallow lollipop gummies. '
                                            'Halvah shortbread cake lemon drops oat cake lollipop candy. Dragée candy '
                                            'jelly donut brownie.',
                                       book=cls.book, owner=user)
