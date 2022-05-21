from pprint import pprint

from django.core.management.base import BaseCommand
from telegram import Bot, Update
from telegram.ext import CallbackContext, Filters, MessageHandler, Updater
from telegram.ext import CallbackQueryHandler
import os
from telegram.utils.request import Request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from django.conf import settings
from django.contrib.auth.models import User

from catalog.management.commands.voice_processing import synthesize, recognize
from catalog.models import Book, Shelf
from catalog.services import scan_isbn, create_book, owners_objects_queryset
from users.models import Profile

DIALOG_STATES = {
    0: 'initial',
    1: 'search',
    2: 'add',
}


def log_errors(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_msg = f'Error occured: {e}'
            print(error_msg)
            raise e

    return inner


def get_last_book_info(profile):
    book = profile.last_book
    keys = {
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
    book_info = '\n'.join([f'{keys[key]}{getattr(book, key)}'
                           for key in keys if getattr(book, key) is not None])
    return book_info


def get_profile_info(profile):
    current_shelf = Shelf.objects.filter(owner=profile.user).first().get_current_shelf()
    return (f'Пользователь: {profile.user.username}\n'
            f'Активный шкаф: {current_shelf.bookcase.title.lower()}\n'
            f'Активная полка: {current_shelf}\n'
            f'Последняя книга: {profile.last_book}\n'
            f'Telegram id: {profile.tele_id}\n')


def get_profile_or_ask_register(chat_id):
    try:
        profile = Profile.objects.get(tele_id=chat_id)
        return profile
    except Exception as e:
        return None


def get_last_book(profile):
    book = profile.last_book
    return book.id


words = {
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


def num_to_words(text):
    values = text.split()
    try:
        result = [value if not value.isdigit() else words[value] for value in values]
        return ' '.join(result)
    except Exception as e:
        print('not in dict')
        return text


@log_errors
def answer(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    reply_text = 'Ошибка1'

    profile = get_profile_or_ask_register(chat_id)
    if profile:
        if profile.state == 0:
            reply_text = 'Вы можете добавить книгу в библиотеку. Для этого у вас должен быть создан книжный шкаф.'
            update.message.reply_text(
                text=reply_text,
                reply_markup=get_add_keyboard() if get_profile_or_ask_register(
                    chat_id).last_book else get_nolastbook_keyboard(), )
        elif profile.state == 1:
            search_answer(chat_id, reply_text, update)
            get_profile_or_ask_register(chat_id).set_dialog_state(0)
        elif profile.state == 2:
            add_book(chat_id, update)
            get_profile_or_ask_register(chat_id).set_dialog_state(0)
    else:
        reply_text = ('Для продолжения работы необходимо зарегистрироваться на сайте и заполнить базу данных. '
                      'Если вы уже зарегистрированы, привяжите ваш телеграм к базе данных.')
        update.message.reply_text(
            text=reply_text,
            reply_markup=get_register_keyboard(chat_id),
        )


def search_answer(chat_id, reply_text, update):
    try:
        file = update.message.voice.get_file()
        file_name = file.download()
        file_path = os.path.join(settings.BASE_DIR, file_name)
        text = recognize(file_path)['result']
        text = num_to_words(text)
        is_voice = True
    except Exception as e:
        text = update.message.text
        is_voice = False

    if text:
        result = owners_objects_queryset(get_profile_or_ask_register(chat_id).user.id, Book, text).first()
        if result:
            bookcase = result.bookcase.title
            shelf = result.shelf.title
            row = result.shelf.row
            author = result.author.name
            reply_text = f'Книга - {result}, автор - {author}, шкаф: {bookcase}, {shelf}, {row} ряд'
        else:
            reply_text = f'По запросу "{text}" не найдено не одной книги в вашей библиотеке'

    if is_voice:
        answer_path = os.path.join(settings.BASE_DIR, 'answer.ogg')
        synthesize(reply_text, answer_path)
        update.message.reply_voice(
            voice=(open(answer_path, 'rb')),
            reply_markup=get_search_edit_info_keyboard(get_profile_or_ask_register(chat_id))
        )
    else:
        update.message.reply_text(
            text=reply_text,
            reply_markup=get_search_edit_info_keyboard(get_profile_or_ask_register(chat_id))
        )


def add_book(chat_id, update):
    user = User.objects.get(profile__tele_id=chat_id)
    try:
        file = update.message.photo[-1].get_file()
        file_name = file.download()
        file_path = os.path.join(settings.BASE_DIR, file_name)
        isbn_number = scan_isbn(file_path)
        os.remove(file_path)
    except Exception as e:
        print(e)
        isbn_number = update.message.text

    if isbn_number:
        book = create_book(user, isbn_number)
        if type(book) is Book:
            create_book(user, isbn_number)
            profile = get_profile_or_ask_register(chat_id)
            update.message.reply_text(
                text='Книга была успешно добавлена в активную полку!'
                     'Вы можете добавить или изменить информацию о книге.'
                     f'Книга:\n{get_last_book_info(profile)}, профиль {profile}, {profile.user.username}, '
                     f'{profile.last_book}',
                reply_markup=get_search_edit_info_keyboard(profile),
            )
        else:
            update.message.reply_text(
                text=book,
                reply_markup=get_add_keyboard()

            )


class Command(BaseCommand):
    help = 'Telegram bot'

    def handle(self, *args, **options):
        request = Request(connect_timeout=0.5, read_timeout=1.0, )
        bot = Bot(request=request, token=os.environ.get('TELEGRAM_TOKEN'), )
        updater = Updater(bot=bot, use_context=True, )

        message_handler_voice = MessageHandler(Filters.voice, answer)
        message_handler_photo = MessageHandler(Filters.photo, answer)
        message_handler_text = MessageHandler(Filters.text, answer)

        buttons_handler = CallbackQueryHandler(callback=keyboard_callback_handler, pass_chat_data=True)

        updater.dispatcher.add_handler(message_handler_voice)
        updater.dispatcher.add_handler(message_handler_photo)
        updater.dispatcher.add_handler(message_handler_text)
        updater.dispatcher.add_handler(buttons_handler)

        updater.start_polling()
        updater.idle()


# КЛАВИАТУРЫ==================================================================
# CB ==> Callback Button
CB_SEARCH = "callback_button_search"
CB_NEW_BOOK = "callback_button_new_book"
CB_NEW_BOOKCASE = "callback_button_new_bookcase"
CB_EDIT = "callback_button_edit"
CB_BOOK_INFO = "callback_button_book_info"
CB_PROFILE_INFO = "callback_button_profile_info"
CB_REGISTER = "callback_button_register"
CB_BIND = "callback_button_bind"

TITLES = {
    CB_SEARCH: "Найти книгу",
    CB_NEW_BOOK: "Добавить книгу",
    CB_NEW_BOOKCASE: "Добавить шкаф",
    CB_EDIT: "Редактировать",
    CB_BOOK_INFO: "Последняя книга",
    CB_PROFILE_INFO: "Мой профиль",
    CB_REGISTER: "Регистрация",
    CB_BIND: "Привязать Telegram",

}


def get_search_edit_info_keyboard(profile):
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CB_EDIT],
                                 # url=f'https://www.google.ru/',
                                 url=f'{os.environ.get("MY_CURRENT_URL")}book/{get_last_book(profile)}/update/',
                                 callback_data=CB_EDIT),
            InlineKeyboardButton(TITLES[CB_BOOK_INFO], callback_data=CB_BOOK_INFO),
        ],
        [
            InlineKeyboardButton(TITLES[CB_PROFILE_INFO], callback_data=CB_PROFILE_INFO),
        ],
        [
            InlineKeyboardButton(TITLES[CB_SEARCH], callback_data=CB_SEARCH),
        ],

    ]
    return InlineKeyboardMarkup(keyboard)


def get_add_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CB_SEARCH], callback_data=CB_SEARCH),
        ],
        [
            InlineKeyboardButton(TITLES[CB_NEW_BOOK], callback_data=CB_NEW_BOOK),
            InlineKeyboardButton(TITLES[CB_NEW_BOOKCASE],
                                 url=f'{os.environ.get("MY_CURRENT_URL")}bookcase/new/',
                                 callback_data=CB_NEW_BOOKCASE),
        ],

    ]
    return InlineKeyboardMarkup(keyboard)


def get_nolastbook_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CB_NEW_BOOK], callback_data=CB_NEW_BOOK),
            InlineKeyboardButton(TITLES[CB_NEW_BOOKCASE],
                                 url=f'{os.environ.get("MY_CURRENT_URL")}bookcase/new/',
                                 callback_data=CB_NEW_BOOKCASE),
        ],

    ]
    return InlineKeyboardMarkup(keyboard)


def get_register_keyboard(chat_id):
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CB_REGISTER],
                                 url=f'{os.environ.get("MY_CURRENT_URL")}register/',
                                 callback_data=CB_REGISTER),
            InlineKeyboardButton(TITLES[CB_BIND],
                                 url=f'{os.environ.get("MY_CURRENT_URL")}bind_tele_id/{chat_id}/',
                                 callback_data=CB_BIND),
        ],

    ]
    return InlineKeyboardMarkup(keyboard)


def keyboard_callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = update.effective_message.chat_id

    profile = get_profile_or_ask_register(chat_id)
    if get_profile_or_ask_register(chat_id):

        if data == CB_NEW_BOOK:
            context.bot.send_message(
                chat_id=chat_id,
                text="Мне нужен номер isbn, или фото штрихкода на книге.",
            )
            profile.set_dialog_state(2)
        else:
            if get_profile_or_ask_register(chat_id).last_book is not None:
                if data == CB_SEARCH:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text="Какую книгу ищем?",
                    )
                    profile.set_dialog_state(1)
                if data == CB_BOOK_INFO:
                    book_info = get_last_book_info(get_profile_or_ask_register(chat_id))
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=book_info,
                        reply_markup=get_add_keyboard(),
                    )
                if data == CB_PROFILE_INFO:
                    profile_info = get_profile_info(get_profile_or_ask_register(chat_id))
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=profile_info,
                        reply_markup=get_add_keyboard(),
                    )

            else:
                context.bot.send_message(
                    chat_id=chat_id,
                    text="В вашей библиотеке нет книг. Вы можете добавить книги в библиотеку с помощью данного бота.",
                    reply_markup=get_nolastbook_keyboard(),
                )

    else:
        context.bot.send_message(
            chat_id=chat_id,
            text='Для продолжения работы необходимо зарегистрироваться на сайте и заполнить базу данных. '
                 'Если вы уже зарегистрированы, привяжите ваш телеграм к базе данных.',
            reply_markup=get_register_keyboard(chat_id),
        )
