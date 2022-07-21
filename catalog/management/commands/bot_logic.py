import os
import re

from django.contrib.auth.models import User

import catalog.services as services
from book_finder import settings
from catalog.management.commands.voice_processing import synthesize, recognize
from catalog.models import Shelf, Book, BookCase
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
        'bookcase': 'Шкаф: ',
        'shelf': 'Местоположение: ',
    }


def get_last_book(chat_id):
    profile = get_profile_or_none(chat_id)
    return profile.last_book


def get_book_info(chat_id, book_id=None):
    profile = get_profile_or_none(chat_id)
    if book_id:
        book = Book.objects.get(pk=book_id)
        if book != profile.last_book:
            profile.last_book = book
            profile.save()
    else:
        book = profile.last_book

    book_info = '\n'.join([f'{BOOK_INFO_KEYS[key]}{getattr(book, key)}'
                           for key in BOOK_INFO_KEYS if getattr(book, key) is not None])
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


def get_profile_or_none(chat_id):
    try:
        profile = Profile.objects.get(tele_id=chat_id)
        return profile
    except Exception as e:
        return None


def delete_book(chat_id):
    profile = get_profile_or_none(chat_id)
    book = profile.last_book
    delete_id = book.id
    book.delete()
    profile.last_book = Book.objects.filter(owner=profile.user.id).exclude(pk=delete_id).last()
    profile.save()


def num_to_words(text):
    values = text.split()
    try:
        result = [value if not value.isdigit() else NUM_WORDS[value] for value in values]
        return ' '.join(result)
    except Exception as e:
        print('not in dict')
        return text


def set_dialog_state(chat_id, state):
    profile = get_profile_or_none(chat_id)
    profile.set_dialog_state(state)


def get_profile_user(chat_id):
    return User.objects.get(profile__tele_id=chat_id)


def get_isbn_from_msg(update):
    try:
        file = update.message.photo[-1].get_file()
        file_name = file.download()
        file_path = os.path.join(settings.BASE_DIR, file_name)
        isbn_number = services.scan_isbn(file_path)
        os.remove(file_path)
    except Exception as e:
        print(e)
        isbn_number = update.message.text
    return isbn_number


def process_search_query(chat_id, query):
    profile = get_profile_or_none(chat_id)
    result = services.owners_objects_queryset(profile.user.id, Book, query).first()
    if result:
        bookcase = result.bookcase.title
        shelf = result.shelf.title
        row = result.shelf.row
        author = result.author.name
        profile.last_book = result
        profile.save()
        return f'Книга - {result}, автор - {author}, шкаф: {bookcase}, {shelf}, {row} ряд'
    else:
        return f'По запросу "{query}" не найдено не одной книги в вашей библиотеке'


def voice_search(file, chat_id, answer_path):
    file_name = file.download()
    file_path = os.path.join(settings.BASE_DIR, file_name)
    text = recognize(file_path)['result']
    query = num_to_words(text)

    reply_text = process_search_query(chat_id, query)
    synthesize(reply_text, answer_path)


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


def get_shelf_list(chat_id, bookcase_id):
    user = get_profile_user(chat_id)
    shelf_list = services.owners_objects_queryset(user, Shelf).filter(bookcase_id=bookcase_id)
    return {shelf.id: shelf for shelf in shelf_list}


def create_book_for_isbn(update, chat_id):
    user = get_profile_user(chat_id)
    isbn_number = get_isbn_from_msg(update)
    if isbn_number is not None:
        book = services.create_book(user, isbn_number)
        if type(book) is Book:
            new_book_msg = f'ID: {book.id}, {book.author} - {book.title} - добавлена'
        else:
            new_book_msg = f'{isbn_number} - не найдено'
    else:
        new_book_msg = 'Не распознан штрих-код на фото'

    return new_book_msg
