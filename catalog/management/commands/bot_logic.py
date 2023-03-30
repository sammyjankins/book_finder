import os
import re

from django.contrib.auth.models import User
import catalog.services as services
from book_finder import settings
from catalog.management.commands.voice_processing import synthesize, recognize
from catalog.models import Shelf, Book, BookCase, Author
from users.models import Profile

NUM_WORDS = {
    '1': 'один',
    '2': 'два',
    '3': 'три',
    '4': 'четыре',
    '5': 'пять',
    '6': 'шесть',
    '7': 'семь',
    '8': 'восемь',
    '9': 'девять',
    '10': 'десять',
    '11': 'одиннадцать',
    '12': 'двенадцать',
    '13': 'тринадцать',
    '14': 'четырнадцать',
    '15': 'пятнадцать',
    '16': 'шестнадцать',
    '17': 'семнадцать',
    '18': 'восемнадцать',
    '19': 'девятнадцать',
    '20': 'двадцать',
}

BOOK_INFO_KEYS = {
    'title': 'Книга: ',
    'author': 'Автор: ',
    'ISBN': 'ISBN: ',
    'year_of_publication': 'Год публикации: ',
    'pages': 'Страниц: ',
    'type_of_cover': 'Тип обложки: ',
    'language': 'Язык: ',
}


def get_last_book(chat_id: str = None, book_id: str = None) -> Book:
    if book_id:
        return Book.objects.get(pk=book_id)
    profile = get_profile_or_none(chat_id)
    queryset = services.owners_objects_queryset(profile.user, Book)
    return queryset.last()


def get_book_info(chat_id=None, book=None, book_id=None):
    if not book:
        book = get_last_book(chat_id, book_id)
    book_info = '\n'.join([f'{BOOK_INFO_KEYS[key]}{getattr(book, key)}'
                           for key in BOOK_INFO_KEYS if getattr(book, key) is not None])
    book_info = f'{book_info}\nШкаф: {book.shelf.bookcase.title}\nМестоположение: {book.shelf}'
    f, r = book.favorite, book.read
    star, check, newline = '\u2B50', '\u2705', '\n'
    book_info = f"{star * f}{check * r}{newline * (f or r)}{book_info}"
    return book_info


def get_profile_info(chat_id):
    profile = get_profile_or_none(chat_id)
    current_shelf = get_current_shelf(chat_id)
    current_shelf_line = f'шкаф - {current_shelf.bookcase.title.lower()}, {current_shelf}'
    return (f'Пользователь: {profile.user.username}\n'
            f'Telegram id: {profile.tele_id}\n'
            f'Активная полка: {current_shelf_line}')


def get_current_shelf(chat_id):
    profile = get_profile_or_none(chat_id)
    current_shelf = Shelf.objects.filter(is_current=True, owner=profile.user).first()
    return current_shelf


def get_shelf(shelf_data, user):
    if shelf_data.get('section_number'):
        section_number = shelf_data.get('section_number')
    else:
        section_number = 1
    shelf = Shelf.objects.filter(bookcase=shelf_data['bookcase_id'],
                                 order_number=shelf_data['order_number'],
                                 row_number=shelf_data['row_number'],
                                 section_number=section_number,
                                 owner=user).first()
    return shelf


def get_current_bookcase(current_shelf):
    return current_shelf.bookcase


def get_profile_or_none(chat_id):
    return Profile.objects.filter(tele_id=chat_id).first()


def delete_book(chat_id):
    book = get_last_book(chat_id)
    book.delete()


def num_to_words(text):
    values = text.split()
    try:
        result = [value if not value.isdigit() else NUM_WORDS[value] for value in values]
        return ' '.join(result)
    except Exception as e:
        print('not in dict')
        return text


def get_profile_user(chat_id):
    return User.objects.get(profile__tele_id=chat_id)


def get_isbn_from_file(f_name):
    file_path = os.path.join(settings.BASE_DIR, f_name)
    isbn_number = services.scan_isbn(file_path)
    os.remove(file_path)
    return isbn_number


def book_to_answer(book_id):
    book = Book.objects.get(id=book_id)
    bookcase = book.shelf.bookcase.title
    shelf = book.shelf.title
    row = book.shelf.row
    author = book.author.name
    return f'Книга - {book}, автор - {author}, шкаф: {bookcase}, {shelf}, {row} ряд'


def process_search_query(chat_id, query):
    profile = get_profile_or_none(chat_id)
    result = services.owners_objects_queryset(profile.user.id, Book, query)[:5]
    if result:
        return {
            book.id: {
                'title': book.title,
                'author': book.author,
                'bookcase': f'{book.shelf.bookcase}',
            } for book in result}
    return None


def voice_search():
    file_path = os.path.join(settings.BASE_DIR, 'request.ogg')
    text = recognize(file_path)['result']
    query = num_to_words(text)
    return query


def get_book_by_id(book_id, chat_id):
    user = get_profile_user(chat_id)
    return services.owners_objects_queryset(user.id, Book).get(pk=book_id)


def extract_book_ids_from_msg(message, chat_id):
    pattern = r'ID: \d+'
    id_s = [result.split()[-1] for result in re.findall(pattern, message)]
    titles = [f'{book.author} - {book.title}' for book_id in id_s if (book := get_book_by_id(book_id, chat_id))]
    return dict(zip(id_s, titles))


def get_bookcase_list(chat_id):
    user = get_profile_user(chat_id)
    bookcase_list = services.owners_objects_queryset(user, BookCase)
    return {bookcase.id: bookcase.title for bookcase in bookcase_list}


def get_shelf_list(chat_id: str, bookcase_id: str) -> dict:
    user = get_profile_user(chat_id)
    shelf_list = services.owners_objects_queryset(user, Shelf).filter(bookcase_id=bookcase_id)

    return {shelf.id: {'title': shelf.title,
                       'row': shelf.row,
                       'is_current': shelf.is_current} for shelf in shelf_list}


def create_book(chat_id, data):
    book_info = {'author': '', 'year_of_publication': '',
                 'type_of_cover': '', 'ISBN': '', 'language': '', 'pages': None, }

    user = get_profile_user(chat_id)
    current_shelf = get_current_shelf(chat_id)

    book_info.update(data)

    if current_shelf:
        book_info.update({'shelf': current_shelf, 'owner': user})

    if book_info['author']:
        author = Author.objects.filter(name=book_info['author'], owner=user).first()
        if author is None:
            author = Author.objects.create(name=book_info['author'], owner=user)
        book_info['author'] = author
        book_info['new_author'] = author.name
        book = Book.objects.create(**book_info)
        return book
    else:
        return None


def create_bookcase(data, user):
    bookcase = BookCase.objects.create(**data, owner=user)
    return bookcase


def get_bookcase_detail(bookcase_id):
    bookcase = BookCase.objects.get(pk=bookcase_id)
    return {
        'id': bookcase_id,
        'title': bookcase.title,
        'shelf_count': bookcase.shelf_count,
        'row_count': bookcase.row_count,
        'section_count': bookcase.section_count,
    }

