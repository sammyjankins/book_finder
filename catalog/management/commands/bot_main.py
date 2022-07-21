import os

from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Bot, Update
from telegram.ext import CallbackContext, Filters, MessageHandler, Updater, CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.utils.request import Request

import catalog.management.commands.bot_logic as bot_logic
import catalog.management.commands.bot_view as keyboards
from catalog.models import Book
from catalog.services import create_book, swap_favorite, swap_read, new_active_shelf

DIALOG_STATES = {
    0: 'initial',
    1: 'search',
    2: 'add',
    3: 'add_group',
}
NEW_LN = '\n'


def log_errors(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_msg = f'Error occured: {e}'
            print(error_msg)
            raise e

    return inner


def help_msg(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    update.message.reply_text(
        text="Этот бот поможет вам быстро найти книгу в вашем шкафу или добавить новую книгу "
             "на активную полку.\nЧтобы добавлять книги, нужно создать шкаф на сайте. Книги будут "
             "добавляться на активную полку, которую можно выбрать на сайте. Для добавления книги "
             "можно отправить фото штрих-кода с ISBN, либо текстовый поисковой запрос, который может "
             "включать в себя номер ISBN, название, автора. Для поиска книги по вашей библиотеке можно "
             "использовать как текстовый, так и голосовой запрос."
        ,
        reply_markup=keyboards.get_add_keyboard() if bot_logic.get_profile_or_none(
            chat_id).last_book else keyboards.get_nolastbook_keyboard(),

    )


@log_errors
def answer(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    profile = bot_logic.get_profile_or_none(chat_id)
    if profile:
        if profile.state == 0:
            reply_text = 'Выберите действие:'
            update.message.reply_text(
                text=reply_text,
                reply_markup=keyboards.get_add_keyboard() if bot_logic.get_profile_or_none(
                    chat_id).last_book else keyboards.get_nolastbook_keyboard(), )
        elif profile.state == 1:
            search_answer(chat_id, update)
            bot_logic.get_profile_or_none(chat_id).set_dialog_state(0)
        elif profile.state == 2:
            add_book(chat_id, update)
            bot_logic.get_profile_or_none(chat_id).set_dialog_state(0)
        elif profile.state == 3:
            add_books(chat_id, update, context.bot)
    else:
        reply_text = ('Для продолжения работы необходимо зарегистрироваться на сайте и заполнить базу данных. '
                      'Если вы уже зарегистрированы, привяжите ваш телеграм к базе данных.')
        update.message.reply_text(
            text=reply_text,
            reply_markup=keyboards.get_register_keyboard(chat_id),
        )


def search_answer(chat_id, update):
    if update.message.voice is not None:

        answer_path = os.path.join(settings.BASE_DIR, 'answer.ogg')
        bot_logic.voice_search(file=update.message.voice.get_file(),
                               chat_id=chat_id,
                               answer_path=answer_path)
        update.message.reply_voice(
            voice=(open(answer_path, 'rb')),
            reply_markup=keyboards.get_search_edit_info_keyboard(chat_id)
        )

    elif update.message.text is not None:
        update.message.reply_text(
            text=bot_logic.process_search_query(chat_id, update.message.text),
            reply_markup=keyboards.get_search_edit_info_keyboard(chat_id)
        )

    else:
        update.message.reply_text(
            text='Боюсь наше общение зашло в тупик. Выберите действие:',
            reply_markup=keyboards.get_add_keyboard() if bot_logic.get_profile_or_none(
                chat_id).last_book else keyboards.get_nolastbook_keyboard(),
        )


def add_book(chat_id, update):
    """Добваление книги. Попытка получить фото и извлечь из него номер isbn. Если ошибка - isbn мог быть
    выслан текстом"""
    user = bot_logic.get_profile_user(chat_id)

    if isbn_number := bot_logic.get_isbn_from_msg(update):
        book = create_book(user, isbn_number)

        # если результат функии create_book - объект класса Book - успех, иначе - сообщение об ошибке.
        if type(book) is Book:
            update.message.reply_text(
                text='Книга была успешно добавлена в активную полку!\n'
                     'Вы можете добавить или изменить информацию о книге. '
                     f'\n{bot_logic.get_book_info(chat_id)}',
                reply_markup=keyboards.get_search_edit_info_keyboard(chat_id),
            )
        else:
            update.message.reply_text(
                text=book,
                reply_markup=keyboards.get_add_keyboard()

            )


def add_books(chat_id, update, bot):
    new_book_msg = bot_logic.create_book_for_isbn(update, chat_id)

    bot.msg_for_edit[chat_id] = bot.edit_message_text(
        text=f"{bot.msg_for_edit[chat_id].text}{NEW_LN}{new_book_msg}",
        chat_id=chat_id,
        message_id=bot.msg_for_edit[chat_id].message_id,
        reply_markup=keyboards.get_done_keyboard(),
    )
    bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)


# CALLBACK FUNCTIONS ============================================================================================

def callback_new_book(bot, chat_id):
    current_shelf = bot_logic.get_current_shelf(chat_id)
    current_shelf_line = f'шкаф - {current_shelf.bookcase.title.lower()}, {current_shelf}'
    bot.send_message(
        chat_id=chat_id,
        text=f"Мне нужен номер isbn, или фото штрихкода на книге. Книга будет добавлена на активную полку ("
             f"{current_shelf_line}).",
    )
    bot_logic.set_dialog_state(chat_id, 2)


def callback_new_active_shelf(bot, chat_id):
    current_shelf = bot_logic.get_current_shelf(chat_id)
    bookcase_dict = bot_logic.get_bookcase_list(chat_id)

    current_shelf_line = f'шкаф - {current_shelf.bookcase.title.lower()}, {current_shelf}'
    bot.send_message(
        chat_id=chat_id,
        text=f"Активная - полка, на которую добавляются книги при использовании бота. Ваша активная полка - "
             f"{current_shelf_line}. Для выбора другой активной полки выберите шкаф: ",
        reply_markup=keyboards.get_bookcase_list_keyboard(bookcase_dict),
    )


def callback_shelf_list(bot, chat_id, bookcase_id):
    current_shelf = bot_logic.get_current_shelf(chat_id)
    shelf_dict = bot_logic.get_shelf_list(chat_id, bookcase_id)
    bot.send_message(
        chat_id=chat_id,
        text="Выберите активную полку:",
        reply_markup=keyboards.get_shelf_list_keyboard(shelf_dict, current_shelf),
    )


def callback_new_book_group(bot, chat_id):
    current_shelf = bot_logic.get_current_shelf(chat_id)
    init_msg = ('Мне нужны фото штрихкодов на книгах либо номера ISBN, по ондому номеру на сообщение. '
                f'Активная полка - {current_shelf}. '
                'Когда закончите добавлять книги нажмите "Готово".')
    message = bot.send_message(
        chat_id=chat_id,
        text=init_msg,
        reply_markup=keyboards.get_back_keyboard(),
    )
    bot.msg_for_edit[chat_id] = message
    bot_logic.set_dialog_state(chat_id, 3)


def callback_search(bot, chat_id):
    bot.send_message(
        chat_id=chat_id,
        text="Какую книгу ищем?",
    )
    bot_logic.set_dialog_state(chat_id, 1)


def callback_book_info(bot, chat_id, book_id=None):
    book_info = bot_logic.get_book_info(chat_id, book_id=book_id)
    bot.send_message(
        chat_id=chat_id,
        text=book_info,
        reply_markup=keyboards.get_search_edit_info_keyboard(chat_id),
    )


def callback_profile_info(bot, chat_id):
    profile_info = bot_logic.get_profile_info(chat_id)
    bot.send_message(
        chat_id=chat_id,
        text=profile_info,
        reply_markup=keyboards.get_add_keyboard(),
    )


def callback_fav(query, chat_id):
    swap_favorite(kwargs={'pk': bot_logic.get_last_book(chat_id).id})
    book_info = bot_logic.get_book_info(chat_id)
    query.edit_message_text(
        text=book_info,
        reply_markup=keyboards.get_search_edit_info_keyboard(chat_id),
    )


def callback_read(query, chat_id):
    swap_read(kwargs={'pk': bot_logic.get_last_book(chat_id).id})
    book_info = bot_logic.get_book_info(chat_id)
    query.edit_message_text(
        text=book_info,
        reply_markup=keyboards.get_search_edit_info_keyboard(chat_id),
    )


def callback_shelf_select(query, chat_id, shelf_id):
    user = bot_logic.get_profile_user(chat_id)
    new_active_shelf(user=user, kwargs={'pk': shelf_id})
    current_shelf = bot_logic.get_current_shelf(chat_id)
    shelf_dict = bot_logic.get_shelf_list(chat_id, current_shelf.bookcase.id)
    query.edit_message_text(
        text="Активная полка изменена. Вы можете выбрать новую активную полку или вернуться к выбору действия:",
        reply_markup=keyboards.get_shelf_list_keyboard(shelf_dict, current_shelf),
    )


def callback_back(bot, chat_id):
    reply_text = 'Выберите действие:'
    bot.send_message(
        chat_id=chat_id,
        text=reply_text,
        reply_markup=keyboards.get_add_keyboard() if bot_logic.get_profile_or_none(
            chat_id).last_book else keyboards.get_nolastbook_keyboard(), )
    bot_logic.set_dialog_state(chat_id, 0)


def callback_delete(bot, chat_id):
    bot_logic.delete_book(chat_id)
    reply_text = 'Книга удалена.'
    bot.send_message(
        chat_id=chat_id,
        text=reply_text,
    )


def callback_done(bot, chat_id):
    message = bot.msg_for_edit[chat_id].text
    books_dict = bot_logic.extract_book_ids_from_msg(message, chat_id)
    del bot.msg_for_edit[chat_id]
    bot.send_message(
        chat_id=chat_id,
        text="Вы можете ознакомиться с любой книгой из добавленных:",
        reply_markup=keyboards.get_new_books_list_keyboard(books_dict)
    )


def keyboard_callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = update.effective_message.chat_id

    profile = bot_logic.get_profile_or_none(chat_id)
    if profile:

        if data == keyboards.CB_NEW_BOOK:
            callback_new_book(context.bot, chat_id)
        if data == keyboards.CB_NEW_BOOK_GROUP:
            callback_new_book_group(context.bot, chat_id)

        else:
            if profile.last_book is not None:
                if data == keyboards.CB_SEARCH:
                    callback_search(context.bot, chat_id)
                if data == keyboards.CB_PROFILE_INFO:
                    callback_profile_info(context.bot, chat_id)
                if data == keyboards.CB_FAV:
                    callback_fav(query, chat_id)
                if data == keyboards.CB_READ:
                    callback_read(query, chat_id)
                if data == keyboards.CB_BACK:
                    callback_back(context.bot, chat_id)
                if data == keyboards.CB_DONE:
                    callback_done(context.bot, chat_id)
                if data == keyboards.CB_DELETE:
                    callback_delete(context.bot, chat_id)
                    callback_back(context.bot, chat_id)
                if data == keyboards.CB_NEW_CURRENT_SHELF:
                    callback_new_active_shelf(context.bot, chat_id)
                if keyboards.CB_SHELVES in data:
                    bookcase_id = data.split('-')[-1]
                    callback_shelf_list(context.bot, chat_id, bookcase_id)
                if keyboards.CB_SHELF_SELECT in data:
                    shelf_id = data.split('-')[-1]
                    callback_shelf_select(query, chat_id, shelf_id)
                if data == keyboards.CB_BOOK_INFO:
                    callback_book_info(context.bot, chat_id)
                elif keyboards.CB_BOOK_INFO in data:
                    book_id = data.split('-')[-1]
                    callback_book_info(context.bot, chat_id, book_id=book_id)
            else:
                context.bot.send_message(
                    chat_id=chat_id,
                    text="В вашей библиотеке нет книг. Вы можете добавить книги в библиотеку с помощью данного бота.",
                    reply_markup=keyboards.get_nolastbook_keyboard(),
                )

    else:
        context.bot.send_message(
            chat_id=chat_id,
            text='Для продолжения работы необходимо зарегистрироваться на сайте и заполнить базу данных. '
                 'Если вы уже зарегистрированы, привяжите ваш телеграм к базе данных.',
            reply_markup=keyboards.get_register_keyboard(chat_id),
        )


class Command(BaseCommand):
    help = 'Telegram bot'

    def handle(self, *args, **options):
        request = Request(connect_timeout=0.5, read_timeout=1.0, )
        bot = Bot(request=request, token=os.environ.get('TELEGRAM_TOKEN'), )
        bot.msg_for_edit = dict()
        updater = Updater(bot=bot, use_context=True, )

        message_handler_voice = MessageHandler(Filters.voice, answer)
        message_handler_photo = MessageHandler(Filters.photo, answer)
        message_handler_text = MessageHandler(Filters.text, answer)

        help_handler = CommandHandler("help", help_msg)

        buttons_handler = CallbackQueryHandler(callback=keyboard_callback_handler, pass_chat_data=True)

        updater.dispatcher.add_handler(message_handler_voice)
        updater.dispatcher.add_handler(message_handler_photo)
        updater.dispatcher.add_handler(message_handler_text)
        updater.dispatcher.add_handler(buttons_handler)
        updater.dispatcher.add_handler(help_handler)

        updater.start_polling()
        updater.idle()
