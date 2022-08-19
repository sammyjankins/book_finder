import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# КЛАВИАТУРЫ==================================================================
# CB ==> Callback Button
from catalog.management.commands import bot_logic

CB_SEARCH = "callback_button_search"
CB_NEW_BOOK = "callback_button_new_book"
CB_NEW_BOOK_GROUP = "callback_button_new_book_group"
CB_NEW_BOOKCASE = "callback_button_new_bookcase"
CB_NEW_CURRENT_SHELF = "callback_button_new_current_shelf"
CB_BOOKCASE_LIST = "callback_button_bookcase_list"
CB_BOOK = "callback_button_edit"
CB_BOOK_INFO = "callback_button_book_info"
CB_SHELVES = "callback_button_shelves"
CB_PROFILE_INFO = "callback_button_profile_info"
CB_REGISTER = "callback_button_register"
CB_BIND = "callback_button_bind"
CB_BINDED = "callback_button_binded"
CB_SITE = "callback_button_site"
CB_FAV = "callback_button_fav"
CB_READ = "callback_button_read"
CB_DELETE = "callback_button_delete"
CB_BACK = "callback_button_back"
CB_DONE = "callback_button_done"
CB_SHELF_SELECT = "callback_shelf_select"

TITLES = {
    CB_SEARCH: "Найти книгу",
    CB_NEW_BOOK: "Добавить книгу",
    CB_NEW_BOOK_GROUP: "Добавить несколько книг",
    CB_NEW_BOOKCASE: "Добавить шкаф (сайт)",
    CB_NEW_CURRENT_SHELF: "Изменить активную полку",
    CB_BINDED: "Готово",
    CB_BOOKCASE_LIST: "Список шкафов",
    CB_BOOK: "Открыть на сайте",
    CB_BOOK_INFO: "Последняя книга (инфо)",
    CB_PROFILE_INFO: "Мой профиль",
    CB_REGISTER: "Регистрация",
    CB_BIND: "Привязать Telegram",
    CB_SITE: "Сайт",
    CB_FAV: "Избранное ",
    CB_READ: "Прочитано ",
    CB_DELETE: "Удалить",
    CB_BACK: "Назад",
    CB_DONE: "Готово",
}


def get_search_edit_info_keyboard(chat_id):
    last_book = bot_logic.get_last_book(chat_id=chat_id)
    star, check = '\u2B50', '\u2705'
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CB_BOOK],
                                 url=f'{os.environ.get("MY_CURRENT_URL")}book/{last_book.id}/',
                                 callback_data=CB_BOOK),
            InlineKeyboardButton(TITLES[CB_SEARCH], callback_data=CB_SEARCH),
        ],
        [
            InlineKeyboardButton(f'{TITLES[CB_FAV]}{star * last_book.favorite}', callback_data=CB_FAV),
            InlineKeyboardButton(f'{TITLES[CB_READ]}{check * last_book.read}', callback_data=CB_READ),
        ],
        [
            InlineKeyboardButton(TITLES[CB_PROFILE_INFO], callback_data=CB_PROFILE_INFO),
            InlineKeyboardButton(TITLES[CB_DELETE], callback_data=CB_DELETE),
        ],
        [
            InlineKeyboardButton(TITLES[CB_BACK], callback_data=CB_BACK),
        ],

    ]
    return InlineKeyboardMarkup(keyboard)


def get_add_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CB_SEARCH], callback_data=CB_SEARCH),
        ],
        [
            InlineKeyboardButton(TITLES[CB_BOOK_INFO], callback_data=CB_BOOK_INFO),
            InlineKeyboardButton(TITLES[CB_PROFILE_INFO], callback_data=CB_PROFILE_INFO),
        ],
        [
            InlineKeyboardButton(TITLES[CB_NEW_CURRENT_SHELF], callback_data=CB_NEW_CURRENT_SHELF),
        ],
        [
            InlineKeyboardButton(TITLES[CB_NEW_BOOK], callback_data=CB_NEW_BOOK),
            InlineKeyboardButton(TITLES[CB_NEW_BOOKCASE],
                                 url=f'{os.environ.get("MY_CURRENT_URL")}bookcase/new/',
                                 callback_data=CB_NEW_BOOKCASE),
        ],
        [
            InlineKeyboardButton(TITLES[CB_NEW_BOOK_GROUP], callback_data=CB_NEW_BOOK_GROUP),
        ],
        [
            InlineKeyboardButton(TITLES[CB_SITE], callback_data=CB_SITE,
                                 url=f'{os.environ.get("MY_CURRENT_URL")}', ),
        ],

    ]
    return InlineKeyboardMarkup(keyboard)


def get_nolastbook_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CB_PROFILE_INFO], callback_data=CB_PROFILE_INFO),
        ],
        [
            InlineKeyboardButton(TITLES[CB_NEW_BOOK], callback_data=CB_NEW_BOOK),
            InlineKeyboardButton(TITLES[CB_NEW_BOOKCASE],
                                 url=f'{os.environ.get("MY_CURRENT_URL")}bookcase/new/',
                                 callback_data=CB_NEW_BOOKCASE),
        ],
        [
            InlineKeyboardButton(TITLES[CB_NEW_CURRENT_SHELF], callback_data=CB_NEW_CURRENT_SHELF),
        ],
        [
            InlineKeyboardButton(TITLES[CB_NEW_BOOK_GROUP], callback_data=CB_NEW_BOOK_GROUP),
        ],
        [
            InlineKeyboardButton(TITLES[CB_SITE], callback_data=CB_SITE,
                                 url=f'{os.environ.get("MY_CURRENT_URL")}', ),
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
        [
            InlineKeyboardButton(TITLES[CB_BINDED],
                                 callback_data=CB_BINDED),
        ],

    ]
    return InlineKeyboardMarkup(keyboard)


def get_no_shelf_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CB_NEW_BOOKCASE],
                                 url=f'{os.environ.get("MY_CURRENT_URL")}bookcase/new/',
                                 callback_data=CB_NEW_BOOKCASE),
        ],

    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CB_BACK], callback_data=CB_BACK),
        ],

    ]
    return InlineKeyboardMarkup(keyboard)


def get_done_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CB_DONE], callback_data=CB_DONE),
        ],

    ]
    return InlineKeyboardMarkup(keyboard)


def get_bookcase_list_keyboard(bookcase_dict):
    buttons = [InlineKeyboardButton(title,
                                    callback_data=f"{CB_SHELVES}-{bookcase_id}")
               for bookcase_id, title in bookcase_dict.items()]
    keyboard = [[button] for button in buttons]
    keyboard.append([InlineKeyboardButton(TITLES[CB_BACK], callback_data=CB_BACK)])
    return InlineKeyboardMarkup(keyboard)


def get_new_books_list_keyboard(books_dict):
    buttons = [InlineKeyboardButton(title,
                                    callback_data=f"{CB_BOOK_INFO}-{book_id}")
               for book_id, title in books_dict.items()]
    keyboard = [[button] for button in buttons]
    keyboard.append([InlineKeyboardButton(TITLES[CB_BACK], callback_data=CB_BACK)])
    return InlineKeyboardMarkup(keyboard)


def get_shelf_list_keyboard(shelf_dict, current_shelf):
    check = '\u2705'
    buttons = [InlineKeyboardButton(f'{str(shelf)} {check if shelf == current_shelf else ""}',
                                    callback_data=f"{CB_SHELF_SELECT}-{shelf_id}")
               for shelf_id, shelf in shelf_dict.items()]
    keyboard = [[button] for button in buttons]
    keyboard.append([InlineKeyboardButton(TITLES[CB_BACK], callback_data=CB_BACK)])
    return InlineKeyboardMarkup(keyboard)
