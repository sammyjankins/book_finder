import os
import logging

from asgiref.sync import sync_to_async

from book_finder import settings
from catalog import services
from catalog.management.commands import bot_logic, voice_processing

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from django.core.management.base import BaseCommand

from catalog.management.commands import bot_constants as bc

# Enable logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Я бот проекта Book Finder. Помогу быстро найти книгу в вашем шкафу или добавить новую "
        "на активную полку.\nДля добавления книг, нужно создать шкаф на сайте. Книги добавляются "
        "по фото штрих-кода ISBN, либо текстовым запросом (ISBN, название или автор). "
        "Для поиска по вашей библиотеке можно использовать как текстовый, так и голосовой запрос."
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def check_profile(func):
    """is telegram tied to a profile on the site"""

    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        profile = await sync_to_async(bot_logic.get_profile_or_none)(chat_id)

        if not profile:
            text = (
                'Для продолжения работы необходимо зарегистрироваться на сайте и заполнить базу данных. '
                'Если вы уже зарегистрированы, привяжите ваш телеграм к базе данных.'
            )
            buttons = [
                [
                    InlineKeyboardButton(text="Регистрация", url='https://www.bookfinder.space/register/'),
                    InlineKeyboardButton(text="Привязать Telegram",
                                         url=f'{os.environ.get("MY_DOMAIN")}bind_tele_id/{chat_id}/'),
                    InlineKeyboardButton(text="Готово", callback_data=str(bc.REGISTER_DONE_CB)),
                ],
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text,
                                           reply_markup=keyboard)
        else:
            return await func(update, context)

    return wrapped


def check_bookcases(func):
    """Checking if the user has bookcases"""

    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        bookcase_list = await sync_to_async(bot_logic.get_bookcase_list)(chat_id)

        if not bookcase_list:
            text = (
                'Для использования этой возможности необходимо создать хотя бы один книжный шкаф.'
            )
            buttons = [
                [
                    InlineKeyboardButton(text="Новый шкаф", callback_data=str(bc.ADD_BOOKCASE_CB)),
                    InlineKeyboardButton(text="Назад", callback_data=str(bc.END_CB)),
                ],
            ]
            keyboard = InlineKeyboardMarkup(buttons)

            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

            return bc.NO_BOOKCASE_STATE
        else:
            return await func(update, context)

    return wrapped


def check_books(func):
    """Checking if the user has bookcases"""

    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        book = await sync_to_async(bot_logic.get_last_book)(chat_id)

        if not book:
            text = (
                'Для использования этой возможности необходимо добавить хотя бы одну книгу в библиотеку.'
            )
            buttons = [
                [
                    InlineKeyboardButton(text="Новые книги", callback_data=str(bc.ADD_BOOKS_START_CB)),
                    InlineKeyboardButton(text="Назад", callback_data=str(bc.END_CB)),
                ],
            ]
            keyboard = InlineKeyboardMarkup(buttons)

            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

            return bc.NO_BOOK_STATE
        else:
            return await func(update, context)

    return wrapped


@check_profile
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Register tele id of select action."""
    if not context.user_data.get(bc.NOT_FIRST_MSG_UD):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Привет! Я помогу быстро найти книгу в вашем шкафу или добавить новую.")
        context.user_data[bc.NOT_FIRST_MSG_UD] = True

    data_to_keep = {
        bc.START_OVER_UD: context.user_data.get(bc.START_OVER_UD),
        bc.LAST_BOOK_UD: context.user_data.get(bc.LAST_BOOK_UD),
        bc.NOT_FIRST_MSG_UD: context.user_data.get(bc.NOT_FIRST_MSG_UD),
    }
    context.user_data.clear()
    context.user_data.update(data_to_keep)

    text = (
        "Выберите действие"
    )

    buttons = [
        [
            InlineKeyboardButton(text="Поиск", callback_data=str(bc.SEARCH_REQUEST_CB)),
        ],
        [
            InlineKeyboardButton(text="Последняя книга", callback_data=str(bc.BOOK_INFO_CB)),
            InlineKeyboardButton(text="Мой профиль", callback_data=str(bc.PROFILE_INFO_CB)),
        ],
        [
            InlineKeyboardButton(text="Новые книги", callback_data=str(bc.ADD_BOOKS_START_CB)),
            InlineKeyboardButton(text="Новый шкаф", callback_data=str(bc.ADD_BOOKCASE_CB)),
        ],
        [
            InlineKeyboardButton(text="Активная полка", callback_data=str(bc.SELECT_BOOKCASE_CB)),
            InlineKeyboardButton(text="Стоп", callback_data=str(bc.END_CB)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    if context.user_data.get(bc.START_OVER_UD):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text,
                                       reply_markup=keyboard)

    context.user_data[bc.START_OVER_UD] = True

    return bc.SELECTING_ACTION_STATE


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """End Conversation by command."""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text="Приятного вам дня!")

    return bc.STOPPING_STATE


async def stop_nested(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Completely end conversation from within nested conversation."""
    await update.message.reply_text("Стоп нестед")

    return bc.STOPPING_STATE


@check_books
async def search_ask_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for book search."""
    text = "Введите поисковой зарос."
    buttons = [
        [
            InlineKeyboardButton(text="Отмена", callback_data=str(bc.END_CB)),
        ],

    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return bc.SEARCH_STATE


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Return search results in the form of text or voice message, depending on the type of request.
    Issuing buttons for interacting with found books."""
    buttons = [
        [
            InlineKeyboardButton(text="Назад", callback_data=str(bc.END_CB)),
        ],
    ]

    # message type definition
    if update.message.text is not None:
        request = update.message.text
        context.user_data[bc.REQUEST_TYPE_UD] = 'TEXT'
    else:
        file = await context.bot.get_file(update.message.voice.file_id)
        await file.download_to_drive(os.path.join(settings.BASE_DIR, 'request.ogg'))
        request = await sync_to_async(bot_logic.voice_search)()
        context.user_data[bc.REQUEST_TYPE_UD] = 'VOICE'

    result = await sync_to_async(bot_logic.process_search_query)(update.message.chat_id, request)

    # determining the number of objects in the search result
    if result:
        if len(result) == 1:
            book_id, book_data = result.popitem()
            context.user_data[bc.LAST_BOOK_UD] = book_id
            text = await sync_to_async(bot_logic.book_to_answer)(book_id)
            buttons[0].append(InlineKeyboardButton(text="Инфо о книге", callback_data=str(bc.BOOK_INFO_CB)))

            state = bc.SEARCH_RESPONSE_STATE

        else:
            text = "Выберите наиболее подходящий вариант из результатов поиска:"
            book_info_buttons = [InlineKeyboardButton(
                f'{data["author"]} - {data["title"]}, {data["bookcase"]}',
                callback_data=f"{bc.BOOK_INFO_CB}-{book_id}")
                for book_id, data in result.items()]
            buttons = [[button] for button in book_info_buttons] + buttons

            state = bc.SEARCH_CHOICE_STATE

    else:
        text = f"Книга по запросу {request} не найдена. Попробуйте еще раз или вернитесь к выбору действий."
        state = bc.SEARCH_STATE

    # context.user_data[START_OVER_UD] = True
    keyboard = InlineKeyboardMarkup(buttons)

    # determining the type of response depending on the type of request
    if context.user_data[bc.REQUEST_TYPE_UD] == 'VOICE':
        answer_path = os.path.join(settings.BASE_DIR, 'answer.ogg')
        await sync_to_async(voice_processing.synthesize)(text, answer_path)
        await update.message.reply_voice(
            voice=(open(answer_path, 'rb')), reply_markup=keyboard
        )
    else:
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[bc.REQUEST_TYPE_UD] = False

    return state


async def get_last_book_from_ud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Getting the last book object to change its state"""
    last_book_id = context.user_data.get(bc.LAST_BOOK_UD)
    last_book = await sync_to_async(bot_logic.get_last_book)(chat_id=update.effective_chat.id, book_id=last_book_id)
    if not last_book_id:
        context.user_data[bc.LAST_BOOK_UD] = last_book.id
    return last_book


async def swap_favorite_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Swapping book state"""
    last_book = await get_last_book_from_ud(update, context)
    await sync_to_async(services.swap_favorite)(kwargs={'pk': last_book.id})
    state = await show_book_info(update, context)
    return state


async def swap_read_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Swapping book state"""
    last_book = await get_last_book_from_ud(update, context)
    await sync_to_async(services.swap_read)(kwargs={'pk': last_book.id})
    state = await show_book_info(update, context)
    return state


async def book_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Deleting a book"""
    await sync_to_async(bot_logic.delete_book)(chat_id=update.effective_chat.id)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text="Книга удалена")
    context.user_data[bc.START_OVER_UD] = False
    context.user_data[bc.LAST_BOOK_UD] = None
    state = await start(update, context)
    return state


@check_books
async def show_book_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Display information about the book and the menu for interacting with it."""
    star, check = '\u2B50', '\u2705'

    if '-' in update.callback_query.data:
        book_id = update.callback_query.data.split('-')[-1]
        context.user_data[bc.LAST_BOOK_UD] = book_id

    last_book = await get_last_book_from_ud(update, context)
    text = await sync_to_async(bot_logic.get_book_info)(update.effective_chat.id, last_book)

    buttons = [
        [
            InlineKeyboardButton(text="Открыть на сайте",
                                 url=f'{os.environ.get("MY_CURRENT_URL")}book/{last_book.id}/'),
            InlineKeyboardButton("Удалить", callback_data=bc.BOOK_DELETE_CB),
        ],
        [
            InlineKeyboardButton(f'Избранное{star * last_book.favorite}', callback_data=bc.FAV_CB),
            InlineKeyboardButton(f'Прочитано{check * last_book.read}', callback_data=bc.READ_CB),
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=str(bc.END_CB)),
        ],

    ]
    keyboard = InlineKeyboardMarkup(buttons)

    if context.user_data.get(bc.START_OVER_UD):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text,
                                       reply_markup=keyboard)
    context.user_data[bc.START_OVER_UD] = True
    return bc.BOOK_INFO_STATE


async def show_profile_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Display information about user profile"""
    text = await sync_to_async(bot_logic.get_profile_info)(update.effective_chat.id)

    buttons = [
        [
            InlineKeyboardButton(text="Поиск", callback_data=str(bc.SEARCH_REQUEST_CB)),
        ],
        [
            InlineKeyboardButton(text="Последняя книга", callback_data=str(bc.BOOK_INFO_CB)),
        ],
        [
            InlineKeyboardButton(text="Назад", callback_data=str(bc.END_CB)),
        ],

    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[bc.START_OVER_UD] = True

    return bc.PROFILE_STATE


@check_bookcases
async def select_bookcase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choosing a bookcase to change the active shelf."""
    current_shelf = await sync_to_async(bot_logic.get_current_shelf)(update.effective_chat.id)
    current_bookcase = await sync_to_async(bot_logic.get_current_bookcase)(current_shelf)
    bookcase_dict = await sync_to_async(bot_logic.get_bookcase_list)(update.effective_chat.id)

    context.user_data[bc.CURRENT_SHELF_UD] = {
        'bookcase': current_bookcase.id,
        'section_number': current_shelf.section_number,
        'order_number': current_shelf.order_number,
        'row_number': current_shelf.row_number,
    }

    current_shelf_line = f'шкаф - {current_bookcase.title.lower()}, {current_shelf}'
    text = ("При добавлении через бота книги попадают на полку: "
            f"{current_shelf_line}. Для выбора другой полки выберите шкаф: ")

    buttons = [InlineKeyboardButton(f'{title} {bc.CHECK if bookcase_id == current_bookcase.id else ""}',
                                    callback_data=f'{bc.BOOKCASE_CB}-{bookcase_id}')
               for bookcase_id, title in bookcase_dict.items()]
    keyboard = [[button] for button in buttons]
    keyboard.append([InlineKeyboardButton(text="Назад", callback_data=str(bc.END_CB))])

    keyboard = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[bc.START_OVER_UD] = True

    return bc.SELECT_BOOKCASE_STATE


async def select_shelf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Display options for a new active shelf from the selected bookcase."""

    callback = update.callback_query.data.split('-')
    bookcase_id = callback[-1]

    context.user_data[bc.SELECTED_SHELF_UD] = {
        'bookcase_id': bookcase_id,
    }

    text = 'Выберите номер полки: '

    context.user_data[bc.SELECTED_BOOKCASE_UD] = await sync_to_async(bot_logic.get_bookcase_detail)(bookcase_id)
    bookcase_data = context.user_data[bc.SELECTED_BOOKCASE_UD]

    if int(bookcase_data['id']) == context.user_data[bc.CURRENT_SHELF_UD]['bookcase']:
        buttons = [[InlineKeyboardButton(f'{services.shelf_titles[i]} '
                                         f'{bc.CHECK if i == context.user_data[bc.CURRENT_SHELF_UD]["order_number"] else ""}',
                                         callback_data=f"{bc.SELECT_SHELF_ORDER_CB}-{i}")]
                   for i in range(1, bookcase_data['shelf_count'] + 1)]
    else:
        buttons = [[InlineKeyboardButton(f'{services.shelf_titles[i]}',
                                         callback_data=f"{bc.SELECT_SHELF_ORDER_CB}-{i}")]
                   for i in range(1, bookcase_data['shelf_count'] + 1)]

    buttons.append([InlineKeyboardButton(text="Назад", callback_data=str(bc.END_CB))])
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return bc.SELECT_SHELF_NUMBER_STATE


async def select_row(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Display options for a new active shelf from the selected bookcase."""

    callback = update.callback_query.data.split('-')
    order_number = callback[-1]

    context.user_data[bc.SELECTED_SHELF_UD]['order_number'] = order_number

    text = 'Выберите номер ряда на полке: '

    bookcase_data = context.user_data[bc.SELECTED_BOOKCASE_UD]

    if (int(bookcase_data['id']) == context.user_data[bc.CURRENT_SHELF_UD]['bookcase'] and
            int(context.user_data[bc.SELECTED_SHELF_UD]['order_number']) == context.user_data[bc.CURRENT_SHELF_UD][
                'order_number']):
        buttons = [[InlineKeyboardButton(f'{services.row_titles[i]} '
                                         f'{bc.CHECK if i == context.user_data[bc.CURRENT_SHELF_UD]["row_number"] else ""}',
                                         callback_data=f"{bc.SELECT_SHELF_ROW_CB}-{i}")]
                   for i in range(1, bookcase_data['row_count'] + 1)]
    else:
        buttons = [[InlineKeyboardButton(f'{services.row_titles[i]} ',
                                         callback_data=f"{bc.SELECT_SHELF_ROW_CB}-{i}")]
                   for i in range(1, bookcase_data['row_count'] + 1)]

    buttons.append([InlineKeyboardButton(text="Назад", callback_data=str(bc.END_CB))])

    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return bc.SELECT_SHELF_ROW_STATE


async def select_section(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Display options for a new active shelf from the selected bookcase."""

    callback = update.callback_query.data.split('-')
    row_number = callback[-1]

    context.user_data[bc.SELECTED_SHELF_UD]['row_number'] = row_number

    bookcase_data = context.user_data[bc.SELECTED_BOOKCASE_UD]
    if bookcase_data['section_count'] == 1:
        return await change_active_shelf(update, context)

    text = 'Выберите секцию на полке: '

    if (int(bookcase_data['id']) == context.user_data[bc.CURRENT_SHELF_UD]['bookcase'] and
            int(context.user_data[bc.SELECTED_SHELF_UD]['order_number']) == context.user_data[bc.CURRENT_SHELF_UD][
                'order_number']
            and int(context.user_data[bc.SELECTED_SHELF_UD]['row_number']) == context.user_data[bc.CURRENT_SHELF_UD][
                'row_number']):
        buttons = [[InlineKeyboardButton(f'{services.sections_titles[i]} '
                                         f'{bc.CHECK if i == context.user_data[bc.CURRENT_SHELF_UD]["section_number"] else ""}',
                                         callback_data=f"{bc.SELECT_SHELF_SECTION_CB}-{i}")]
                   for i in range(1, bookcase_data['section_count'] + 1)]
    else:
        buttons = [[InlineKeyboardButton(f'{services.sections_titles[i]} ',
                                         callback_data=f"{bc.SELECT_SHELF_SECTION_CB}-{i}")]
                   for i in range(1, bookcase_data['section_count'] + 1)]

    buttons.append([InlineKeyboardButton(text="Назад", callback_data=str(bc.END_CB))])

    keyboard = InlineKeyboardMarkup(buttons)
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return bc.SELECT_SHELF_SECTION_STATE


async def change_active_shelf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Saving information about the new active shelf."""

    if bc.SELECT_SHELF_SECTION_CB in update.callback_query.data:
        section_number = update.callback_query.data.split('-')[-1]
        context.user_data[bc.SELECTED_SHELF_UD]['section_number'] = section_number

    shelf_data = context.user_data[bc.SELECTED_SHELF_UD]
    user = await sync_to_async(bot_logic.get_profile_user)(update.effective_chat.id)
    shelf = await sync_to_async(bot_logic.get_shelf)(shelf_data, user)
    await sync_to_async(services.new_active_shelf)(user=user, kwargs={'pk': shelf.id})

    current_bookcase = await sync_to_async(bot_logic.get_bookcase_detail)(shelf_data['bookcase_id'])

    current_shelf_line = f'шкаф - {current_bookcase["title"].lower()}, {shelf}'

    text = f'Новая активная полка: {current_shelf_line}.'

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    context.user_data[bc.START_OVER_UD] = False

    return await start(update, context)


@check_bookcases
async def add_books_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to send ISBN number or photo to add books."""
    current_shelf = await sync_to_async(bot_logic.get_current_shelf)(update.effective_chat.id)
    current_bookcase = await sync_to_async(bot_logic.get_current_bookcase)(current_shelf)
    current_shelf_line = f'шкаф - {current_bookcase.title.lower()}, {current_shelf}'

    context.user_data[bc.ADD_BOOKS_UD] = dict()

    text = ('Мне нужен номер ISBN (фото или текст), либо название книги. Следует давать не более одного запроса '
            f'на сообщение. Активная полка - {current_shelf_line}. '
            'Когда закончите - нажмите "Готово". Для отмены - нажмите "Отмена".')

    buttons = [
        [
            InlineKeyboardButton(text="Отмена", callback_data=str(bc.END_CB)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.callback_query.answer()
    message = await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    context.user_data[bc.BOOKS_MSG_UD] = {'text': message.text,
                                          'message_id': message.message_id,
                                          'chat_id': message.chat_id, }

    return bc.ADD_BOOKS_START_STATE


async def add_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """ISBN number processing and list replenishment."""
    if update.message.text is not None:
        isbn = update.message.text
    else:
        file = await context.bot.get_file(update.message.photo[-1].file_id)
        f_name = file.file_path.split('/')[-1]
        await file.download_to_drive(os.path.join(settings.BASE_DIR, file.file_path.split('/')[-1]))
        isbn = await sync_to_async(bot_logic.get_isbn_from_file)(f_name)

    search_result = services.look_for_response(isbn)
    book_info = services.look_for_response(isbn)
    context.user_data[bc.ADD_BOOKS_UD][book_info['ISBN']] = book_info

    if search_result:
        new_book_msg = f'{search_result["author"]} - {search_result["title"]}'
    else:
        new_book_msg = 'Нет данных'

    text = f'{context.user_data[bc.BOOKS_MSG_UD]["text"]}{bc.NEW_LN}{new_book_msg}'

    buttons = [
        [
            InlineKeyboardButton(text="Готово", callback_data=str(bc.ADD_BOOKS_DONE_CB)),
        ],
        [
            InlineKeyboardButton(text="Отмена", callback_data=str(bc.END_CB)),
        ],
    ]

    keyboard = InlineKeyboardMarkup(buttons)
    await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    message = await context.bot.edit_message_text(text=text,
                                                  chat_id=update.message.chat_id,
                                                  message_id=context.user_data[
                                                      bc.BOOKS_MSG_UD]["message_id"],
                                                  reply_markup=keyboard)
    context.user_data[bc.BOOKS_MSG_UD] = {'text': message.text,
                                          'message_id': message.message_id,
                                          'chat_id': message.chat_id, }

    return bc.ADD_BOOKS_STATE


async def create_found_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Creating books in the database from the found data. Issuing buttons for interacting with added books."""
    buttons = []

    text = 'Вы можете ознакомиться с любой книгой из добавленных: '

    for _, data in context.user_data[bc.ADD_BOOKS_UD].items():
        book = await sync_to_async(bot_logic.create_book)(context.user_data[bc.BOOKS_MSG_UD]["chat_id"], data)
        if book:
            buttons.append([InlineKeyboardButton(
                f'{data["author"]} - {data["title"]}',
                callback_data=f"{bc.BOOK_INFO_CB}-{book.id}")])

    buttons.append([InlineKeyboardButton(text="Главное меню", callback_data=str(bc.END_CB))])
    keyboard = InlineKeyboardMarkup(buttons)

    await context.bot.edit_message_text(text=text,
                                        chat_id=context.user_data[bc.BOOKS_MSG_UD]["chat_id"],
                                        message_id=context.user_data[bc.BOOKS_MSG_UD]["message_id"],
                                        reply_markup=keyboard)

    del context.user_data[bc.ADD_BOOKS_UD]

    return bc.ADD_BOOKS_FINAL_STATE


async def create_bookcase_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Request information about the cabinet to create."""
    bookcase_info = context.user_data.get(bc.BOOKCASE_CREATE_UD)
    if not bookcase_info:
        bookcase_info = context.user_data[bc.BOOKCASE_CREATE_UD] = {
            'title': None,
            'shelf_count': None,
            'row_count': None,
            'section_count': None,
        }
    text = (
        f'Для создания шкафа нужно указать характеристики: {bc.NEW_LN}'
        f'Название: {bookcase_info.get("title") or "Не указано"}{bc.NEW_LN}'
        f'Количество полок: {bookcase_info.get("shelf_count") or "Не указано"}{bc.NEW_LN}'
        f'Рядов на полке: {bookcase_info.get("row_count") or "Не указано"}{bc.NEW_LN}'
        f'Секций на полке: {bookcase_info.get("section_count") or "Не указано"}{bc.NEW_LN}'
    )

    buttons = [
        [
            InlineKeyboardButton(text="Название", callback_data=str(bc.NEW_BOOKCASE_TITLE_CB)),
            InlineKeyboardButton(text="# полок", callback_data=f'{bc.NEW_BOOKCASE_FEATURE_CB}-0'),
        ],
        [
            InlineKeyboardButton(text="# рядов", callback_data=f'{bc.NEW_BOOKCASE_FEATURE_CB}-1'),
            InlineKeyboardButton(text="# секций", callback_data=f'{bc.NEW_BOOKCASE_FEATURE_CB}-2'),
        ],
    ]

    if all((bookcase_info.get("title"), bookcase_info.get("shelf_count"),
            bookcase_info.get("row_count"), bookcase_info.get("section_count"))):
        buttons.append([InlineKeyboardButton(text="Готово", callback_data=str(bc.BOOKCASE_SAVE_CB)), ])

    buttons.append([InlineKeyboardButton(text="Отмена", callback_data=str(bc.END_CB)), ])

    keyboard = InlineKeyboardMarkup(buttons)
    if context.user_data.get(bc.START_OVER_UD):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text=text, reply_markup=keyboard)
    context.user_data[bc.START_OVER_UD] = True

    return bc.ADD_BOOKCASE_STATE


async def new_bookcase_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input bookcase title."""
    text = "Введите название нового шкафа: "
    buttons = [
        [
            InlineKeyboardButton(text="Отмена", callback_data=str(bc.END_CB)),
        ],

    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return bc.TYPING


async def save_bookcase_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Saving bookcase title data."""
    context.user_data[bc.BOOKCASE_CREATE_UD]['title'] = update.message.text
    context.user_data[bc.START_OVER_UD] = False

    return await create_bookcase_start(update, context)


async def new_bookcase_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to select a value for the selected bookcase feature."""
    features = {
        '0': {
            'text': 'полок',
            'feature': 'shelf_count',
            'max_amount': 10,
            'callback': bc.SHELF_COUNT_CB,
        },
        '1': {
            'text': 'рядов',
            'feature': 'row_count',
            'max_amount': 4,
            'callback': bc.ROW_COUNT_CB,
        },
        '2': {
            'text': 'секций',
            'feature': 'section_count',
            'max_amount': 2,
            'callback': bc.SECTIONS_COUNT_CB,
        },
    }
    feature = update.callback_query.data.split('-')[-1]
    context.user_data[bc.CURRENT_FEATURE_UD] = features[feature]['feature']

    buttons = [
        [InlineKeyboardButton(f'{i}', callback_data=f"{features[feature]['callback']}-{i}"),
         InlineKeyboardButton(f'{i + 1}', callback_data=f"{features[feature]['callback']}-{i + 1}")]
        for i in range(1, features[feature]['max_amount'] + 1, 2)
    ]
    buttons.append([InlineKeyboardButton(text="Назад", callback_data=str(bc.END_CB))])

    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=f'Выберите количество {features[feature]["text"]}:',
                                                  reply_markup=keyboard)

    return bc.BOOKCASE_FEATURES_STATE


async def save_bookcase_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Saving selected value for the selected bookcase feature."""
    callback = update.callback_query.data.split('-')
    context.user_data[bc.BOOKCASE_CREATE_UD][context.user_data[bc.CURRENT_FEATURE_UD]] = int(callback[1])
    return await create_bookcase_start(update, context)


async def save_bookcase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Creating a boockase in the database and displaying a message about the new active shelf."""
    user = await sync_to_async(bot_logic.get_profile_user)(update.effective_chat.id)

    bookcase_features = context.user_data[bc.BOOKCASE_CREATE_UD]
    bookcase = await sync_to_async(bot_logic.create_bookcase)(bookcase_features, user)
    current_shelf = await sync_to_async(bot_logic.get_current_shelf)(update.effective_chat.id)

    current_shelf_line = f'шкаф - {bookcase.title.lower()}, {current_shelf}'
    text = f'Шкаф "{bookcase.title}" сохранен. Новая активная полка: {current_shelf_line}.'

    buttons = [
        [
            InlineKeyboardButton(text="Назад", callback_data=str(bc.END_CB)),
        ],

    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return bc.SELECTING_ACTION_STATE


class Command(BaseCommand):
    help = 'Telegram bot'

    def handle(self, *args, **options):
        """Run the bot."""

        application = Application.builder().token(os.environ.get('TELEGRAM_TOKEN')).build()

        book_info_handlers = [
            CallbackQueryHandler(swap_favorite_handler, pattern="^" + str(bc.FAV_CB) + "$"),
            CallbackQueryHandler(swap_read_handler, pattern="^" + str(bc.READ_CB) + "$"),
            CallbackQueryHandler(book_delete_handler, pattern="^" + str(bc.BOOK_DELETE_CB) + "$"),
        ]

        search_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(search_ask_request, pattern="^" + str(bc.SEARCH_REQUEST_CB) + "$"),
            ],
            states={
                bc.SEARCH_STATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, search),
                    MessageHandler(filters.VOICE, search)
                ],
                bc.SEARCH_CHOICE_STATE: [
                    CallbackQueryHandler(show_book_info, pattern="^" + str(bc.BOOK_INFO_CB) + "-[0-9]+$"),
                ],
                bc.SEARCH_RESPONSE_STATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, search),
                ],
                bc.NO_BOOK_STATE: [
                    CallbackQueryHandler(add_books_start, pattern="^" + str(bc.ADD_BOOKS_START_CB) + "$"),
                ],
            },
            fallbacks=[
                CallbackQueryHandler(show_book_info, pattern="^" + str(bc.BOOK_INFO_CB) + "$"),
                CallbackQueryHandler(start, pattern="^" + str(bc.END_CB) + "$"),
                CommandHandler("stop", stop_nested),
            ],
            map_to_parent={
                bc.BOOK_INFO_STATE: bc.BOOK_INFO_STATE,
                bc.END_CB: bc.SELECTING_ACTION_STATE,
                bc.STOPPING_STATE: bc.STOPPING_STATE,
                bc.SELECTING_ACTION_STATE: bc.SELECTING_ACTION_STATE,
            },
        )

        selection_handlers = [
            search_conv,
            CallbackQueryHandler(show_book_info, pattern="^" + str(bc.BOOK_INFO_CB) + "$"),
            CallbackQueryHandler(show_profile_info, pattern="^" + str(bc.PROFILE_INFO_CB) + "$"),
            CallbackQueryHandler(show_profile_info, pattern="^" + str(bc.SEARCH_REQUEST_CB) + "$"),
            CallbackQueryHandler(select_bookcase, pattern="^" + str(bc.SELECT_BOOKCASE_CB) + "$"),
            CallbackQueryHandler(add_books_start, pattern="^" + str(bc.ADD_BOOKS_START_CB) + "$"),
            CallbackQueryHandler(create_bookcase_start, pattern="^" + str(bc.ADD_BOOKCASE_CB) + "$"),
        ]

        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                CallbackQueryHandler(start, pattern="^" + str(bc.REGISTER_DONE_CB) + "$")
            ],
            states={
                bc.SELECTING_ACTION_STATE: selection_handlers,
                bc.BOOK_INFO_STATE: book_info_handlers,
                bc.NO_BOOKCASE_STATE: [
                    CallbackQueryHandler(create_bookcase_start, pattern="^" + str(bc.ADD_BOOKCASE_CB) + "$"),
                ],
                bc.NO_BOOK_STATE: [
                    CallbackQueryHandler(add_books_start, pattern="^" + str(bc.ADD_BOOKS_START_CB) + "$"),
                ],
                bc.PROFILE_STATE: [
                    search_conv,
                    CallbackQueryHandler(show_book_info, pattern="^" + str(bc.BOOK_INFO_CB) + "$"),
                ],
                bc.SELECT_BOOKCASE_STATE: [
                    CallbackQueryHandler(select_shelf, pattern="^" + str(bc.BOOKCASE_CB) + "-[0-9]+$"),
                ],
                bc.SELECT_SHELF_NUMBER_STATE: [
                    CallbackQueryHandler(select_row, pattern="^" + str(bc.SELECT_SHELF_ORDER_CB) + "-[0-9]+$"),
                ],
                bc.SELECT_SHELF_ROW_STATE: [
                    CallbackQueryHandler(select_section, pattern="^" + str(bc.SELECT_SHELF_ROW_CB) + "-[0-9]+$"),
                ],
                bc.SELECT_SHELF_SECTION_STATE: [
                    CallbackQueryHandler(change_active_shelf,
                                         pattern="^" + str(bc.SELECT_SHELF_SECTION_CB) + "-[0-9]+$"),
                ],
                bc.ADD_BOOKS_START_STATE: [
                    MessageHandler(filters.PHOTO, add_books),
                    MessageHandler(filters.TEXT, add_books),
                ],
                bc.ADD_BOOKS_STATE: [
                    MessageHandler(filters.PHOTO, add_books),
                    MessageHandler(filters.TEXT, add_books),
                    CallbackQueryHandler(create_found_books, pattern="^" + str(bc.ADD_BOOKS_DONE_CB) + "$"),
                ],
                bc.ADD_BOOKS_FINAL_STATE: [
                    CallbackQueryHandler(show_book_info, pattern="^" + str(bc.BOOK_INFO_CB) + "-[0-9]+$"),
                ],
                bc.ADD_BOOKCASE_STATE: [
                    CallbackQueryHandler(new_bookcase_title, pattern="^" + str(bc.NEW_BOOKCASE_TITLE_CB) + "$"),
                    CallbackQueryHandler(save_bookcase, pattern="^" + str(bc.BOOKCASE_SAVE_CB) + "$"),
                    CallbackQueryHandler(new_bookcase_feature,
                                         pattern="^" + str(bc.NEW_BOOKCASE_FEATURE_CB) + "-[0-2]+$"),

                ],
                bc.TYPING: [
                    MessageHandler(filters.TEXT, save_bookcase_title),
                    CallbackQueryHandler(create_bookcase_start, pattern="^" + str(bc.END_CB) + "$"),
                ],
                bc.BOOKCASE_FEATURES_STATE: [
                    CallbackQueryHandler(create_bookcase_start, pattern="^" + str(bc.END_CB) + "$"),
                    CallbackQueryHandler(save_bookcase_feature, pattern="^" + str(bc.SHELF_COUNT_CB) + "-[0-9]|10+$"),
                    CallbackQueryHandler(save_bookcase_feature, pattern="^" + str(bc.ROW_COUNT_CB) + "-[0-4]+$"),
                    CallbackQueryHandler(save_bookcase_feature, pattern="^" + str(bc.SECTIONS_COUNT_CB) + "-[0-2]+$"),
                ],
                bc.STOPPING_STATE: [
                    CommandHandler("start", start)
                ],

            },
            fallbacks=[
                CommandHandler("stop", stop),
                CallbackQueryHandler(start, pattern="^" + str(bc.END_CB) + "$"),
            ],
        )

        application.add_handler(conv_handler)
        application.run_polling()
