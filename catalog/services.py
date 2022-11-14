from PIL import Image
from django.contrib import messages
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from pyzbar.pyzbar import decode as p_decode

from catalog.models import Shelf, BookCase, Author, Book
from catalog.parser import GoogleRequestSearch
from users.models import Profile

shelf_titles = {
    1: 'Первая',
    2: 'Вторая',
    3: 'Третья',
    4: 'Четвертая',
    5: 'Пятая',
    6: 'Шестая',
    7: 'Седьмая',
    8: 'Восьмая',
    9: 'Девятая',
    10: 'Десятая',
}
row_titles = {
    1: 'Первый',
    2: 'Второй',
    3: 'Третий',
    4: 'Четвертый',
}

sections_titles = {
    1: 'левая',
    2: 'правая',
}

error_fields = {
    'title': 'Название',
    'author': 'Автор',
    'bookcase': 'Кшижный шкаф',
    'shelf': 'Местоположение в шкафу',
}

search_models = {
    'шкаф': BookCase,
    'автор': Author,
    'книга': Book,
}


def set_owner(request, form):
    form.instance.owner = request.user


def check_owership(instance):
    item = instance.get_object()
    if instance.request.user == item.owner:
        return True
    return False


def new_author(request, form):
    if form.instance.new_author is not None:
        author = Author.objects.filter(name=form.instance.new_author, owner=request.user).first()
        if author is None:
            author = Author.objects.create(name=form.instance.new_author, owner=request.user)
        form.instance.author = author


def check_author(request):
    if request.POST['new_author']:
        return True
    else:
        return False


def new_active_shelf(user=None, kwargs=None):
    active_shelves = Shelf.objects.filter(is_current=True, owner=user)
    for shelf in active_shelves:
        shelf.is_current = False
        shelf.save()
    if kwargs:
        new_active = Shelf.objects.get(pk=kwargs['pk'])
    else:
        new_active = Shelf.objects.last()
    new_active.is_current = True
    new_active.save()


def create_shelves(bookcase):
    for shelf_number in range(bookcase.shelf_count):
        for row_number in range(bookcase.row_count):
            for sections_number in range(bookcase.section_count):
                if bookcase.section_count > 1:
                    section = " слева" if sections_number + 1 == 1 else " справа"
                else:
                    section = ''
                Shelf.objects.create(
                    title=f'{shelf_titles[shelf_number + 1]} полка{section}',
                    row=row_titles[row_number + 1],
                    bookcase=bookcase,
                    owner=bookcase.owner)
    new_active_shelf(user=bookcase.owner)


def owners_objects_queryset(user, Class, question=None):
    objects = Class.objects.all().filter(owner=user)
    if question is not None:
        kwargs = {
            f'{"name" if Class == Author else "title"}__lower__contains': question.lower(), }
        objects = objects.filter(**kwargs)

    return objects.order_by('-id')


def get_favorite_queryset(request):
    return Book.objects.all().filter(owner=request.user, favorite=True)


def get_read_queryset(request):
    return Book.objects.all().filter(owner=request.user, read=True)


def get_unread_queryset(request):
    return Book.objects.all().filter(owner=request.user, read=False)


def global_queryset(request):
    objects = {key: owners_objects_queryset(request.user, Class=Class, question=request.GET.get('q'))
               for key, Class in {'bookcase': BookCase, 'author': Author, 'book': Book}.items()}

    return objects


def get_queryset_for_book_create(request, original_context):
    objects = {key: Class_.objects.all().filter(owner=request.user)
               for key, Class_ in {'bookcase': BookCase, 'author': Author}.items()}
    objects.update({'books': Book.objects.all().distinct('title'),
                    'active': Shelf.objects.filter(owner=request.user).first().get_current_shelf()})
    if errors := original_context['form'].errors:
        objects.update({'errors': {error_fields[key]: value for key, value in errors.items()}})
    return objects


def get_queryset_for_book_update(request, current_object, original_context):
    objects = get_queryset_for_book_create(request, original_context)
    objects.update({'book': current_object})
    return objects


def get_shelves_ajax(request):
    bookcase_id = request.POST['bookcase_id']
    try:
        bookcase = BookCase.objects.get(id=bookcase_id)
        shelves = bookcase.shelves
    except Exception as e:
        print(e)
        data = dict()
        data['error_message'] = 'error'
        return JsonResponse(data)
    return JsonResponse(list(shelves.values('id', 'title', 'row')), safe=False)


def get_book_ajax(request):
    book_title = request.POST['title']
    try:
        book = Book.objects.all().filter(title=book_title).first()
        book_dict = model_to_dict(book, fields=[field.name for field in book._meta.fields])
    except Exception as e:
        print(e)
        data = dict()
        data['error_message'] = 'error'
        return JsonResponse(data)
    return JsonResponse(book_dict, safe=False)


def scan_isbn(img_file):
    barcode_pic = Image.open(img_file)
    decoded = p_decode(barcode_pic)
    try:
        return decoded[0].data.decode()
    except Exception as e:
        print(e)
        return None


def look_for_response(query):
    try:
        searcher = GoogleRequestSearch(query)
        searcher.search()
        return searcher.book_info
    except Exception as e:
        print(e)


def parse_book(request):
    try:
        query = request.POST['query']

        parsed = look_for_response(query)
        if parsed is not None:
            return JsonResponse(parsed, safe=False)
        else:
            return JsonResponse({'error_message': 'Не удалось найти книгу по вашему запросу'})
    except Exception as e:
        print(e)
        return JsonResponse({'error_message': 'Не удалось найти книгу по вашему запросу'})


def create_book(user, isbn_number):
    try:
        current_shelf = Shelf.objects.filter(owner=user).first().get_current_shelf()
        book_info = {'author': '', 'year_of_publication': '',
                     'type_of_cover': '', 'ISBN': '', 'language': '', 'pages': None, }

        parsed = look_for_response(isbn_number)
        if parsed is None:
            return f'Не удалось найти данные по запросу'
        else:
            book_info.update(parsed)
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
                return f'Не указан автор'
    except Exception as e:
        print(e)
        return f'Необходимо создать шкаф для добавления книг'


def book_from_isbn(request):
    isbn = scan_isbn(request.FILES['barcode'])
    if isbn is None:
        messages.warning(request, 'Штрихкод на изображении не удалось распознать')
        return HttpResponseRedirect(reverse('book-create'))

    book = create_book(request.user, isbn)
    if type(book) is Book:
        messages.success(request, 'Книга была успешно добавлена в активную полку!\n'
                                  'Вы можете добавить или изменить информацию о книге.')
        return HttpResponseRedirect(reverse('book-update', args=[book.id]))
    else:
        messages.warning(request, book)
        return HttpResponseRedirect(reverse('book-create'))


def swap_favorite(kwargs):
    book = Book.objects.get(pk=kwargs['pk'])
    book.favorite = False if book.favorite else True
    book.save()


def swap_read(kwargs):
    book = Book.objects.get(pk=kwargs['pk'])
    book.read = False if book.read else True
    book.save()


def last_book_delete(request, **kwargs):
    profile = Profile.objects.get(user=request.user)
    if profile.last_book.pk == kwargs['pk']:
        profile.last_book = Book.objects.filter(owner=request.user).exclude(pk=profile.last_book.pk).last()
        profile.save()


def change_active_shelf(request, **kwargs):
    new_active = Shelf.objects.exclude(bookcase_id=kwargs['pk']).filter(owner=request.user).first()
    if new_active:
        new_active.is_current = True
        new_active.save()


if __name__ == '__main__':
    with open('../media/2cJydo9UIZU.jpg', mode='r') as f:
        a = scan_isbn(f)
        print(a)
