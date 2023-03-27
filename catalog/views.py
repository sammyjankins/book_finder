from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

import catalog.services as logic
from catalog.models import BookCase, Shelf, Author, Book, Note


class BookcaseListView(ListView):
    model = BookCase
    template_name = 'catalog/home.html'
    context_object_name = 'results'
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        return logic.owners_objects_queryset(self.request.user, BookCase, question=self.request.GET.get('q'))


class AuthorListView(ListView):
    model = Author
    template_name = 'catalog/author_list.html'
    context_object_name = 'authors'
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        return logic.owners_objects_queryset(self.request.user, Author, question=self.request.GET.get('q'))


class BookListView(ListView):
    model = Book
    template_name = 'catalog/book_list.html'
    context_object_name = 'results'
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        return logic.owners_objects_queryset(self.request.user, Book, question=self.request.GET.get('q'))


class FavoriteListView(ListView):
    model = Book
    template_name = 'catalog/book_list.html'
    context_object_name = 'results'
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        return logic.get_favorite_queryset(self.request)


class ReadListView(ListView):
    model = Book
    template_name = 'catalog/book_list.html'
    context_object_name = 'results'
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        return logic.get_read_queryset(self.request)


class UnreadListView(ListView):
    model = Book
    template_name = 'catalog/book_list.html'
    context_object_name = 'results'
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        return logic.get_unread_queryset(self.request)


class SearchListView(ListView):
    model = Book
    template_name = 'catalog/search_list.html'
    context_object_name = 'results'

    def get_queryset(self, *args, **kwargs):
        return logic.global_queryset(self.request)


class BookcaseDetailView(UserPassesTestMixin, DetailView):
    model = BookCase

    def test_func(self):
        return logic.check_owership(self)


class ShelfDetailView(UserPassesTestMixin, DetailView):
    model = Shelf

    def test_func(self):
        return logic.check_owership(self)


class AuthorDetailView(UserPassesTestMixin, DetailView):
    model = Author

    def test_func(self):
        return logic.check_owership(self)


class BookDetailView(UserPassesTestMixin, DetailView):
    model = Book

    def test_func(self):
        return logic.check_owership(self)


class BookcaseCreateView(CreateView):
    model = BookCase
    fields = ['title', 'shelf_count', 'section_count', 'row_count', ]

    def form_valid(self, form):
        logic.set_owner(self.request, form)
        return super().form_valid(form)


class AuthorCreateView(CreateView):
    model = Author
    fields = ['name', 'date_of_birth', 'country', ]

    def form_valid(self, form):
        logic.set_owner(self.request, form)
        return super().form_valid(form)


class BookCreateView(CreateView):
    model = Book
    context_object_name = 'objects'
    fields = ['title', 'pages', 'year_of_publication', 'language',
              'ISBN', 'type_of_cover', 'shelf', 'new_author', 'annotation', ]
    template_name = 'catalog/book_create.html'

    def post(self, request, **kwargs):
        if request.FILES:
            return logic.book_from_isbn(request)
        if not logic.check_author(request):
            messages.warning(request, 'Автор не указан!')
            return HttpResponseRedirect(reverse('book-create'))
        return super(BookCreateView, self).post(request, **kwargs)

    def form_valid(self, form):
        logic.set_owner(self.request, form)
        logic.new_author(self.request, form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return logic.get_queryset_for_book_create(self.request, ctx)


class NoteCreateView(CreateView):
    model = Note
    fields = ['text', 'book']
    template_name = 'catalog/book_detail.html'

    def form_valid(self, form):
        logic.set_owner(self.request, form)
        return super().form_valid(form)


class BookcaseUpdateView(UserPassesTestMixin, UpdateView):
    model = BookCase
    fields = ['title', ]

    def test_func(self):
        return logic.check_owership(self)


class ShelfUpdateView(UserPassesTestMixin, UpdateView):
    model = Shelf
    fields = ['title', ]

    def test_func(self):
        return logic.check_owership(self)

    def form_valid(self, form):
        return super().form_valid(form)


class AuthorUpdateView(UserPassesTestMixin, UpdateView):
    model = Author
    fields = ['name', 'date_of_birth', 'country', ]

    def test_func(self):
        return logic.check_owership(self)


class BookUpdateView(UserPassesTestMixin, UpdateView):
    model = Book
    context_object_name = 'objects'
    fields = ['title', 'pages', 'year_of_publication', 'language',
              'ISBN', 'type_of_cover', 'shelf', 'new_author', 'annotation', ]
    template_name = 'catalog/book_update.html'

    def test_func(self):
        return logic.check_owership(self)

    def form_valid(self, form):
        logic.new_author(self.request, form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return logic.get_queryset_for_book_update(self.request, self.object, ctx)


class NoteUpdateView(UserPassesTestMixin, UpdateView):
    model = Note
    fields = ['text', ]
    template_name = 'catalog/book_detail.html'

    def test_func(self):
        return logic.check_owership(self)

    def get_success_url(self):
        return reverse('book-detail', kwargs={'pk': self.get_object().book.pk})


class BookcaseDeleteView(UserPassesTestMixin, DeleteView):
    model = BookCase
    success_url = '/'

    def test_func(self):
        return logic.check_owership(self)


class AuthorDeleteView(UserPassesTestMixin, DeleteView):
    model = Author
    success_url = '/author/all'

    def test_func(self):
        return logic.check_owership(self)


class BookDeleteView(UserPassesTestMixin, DeleteView):
    model = Book
    success_url = '/book/all'

    def test_func(self):
        return logic.check_owership(self)


class NoteDeleteView(UserPassesTestMixin, DeleteView):
    model = Note

    def test_func(self):
        return logic.check_owership(self)

    def get_success_url(self):
        return reverse('book-detail', kwargs={'pk': self.get_object().book.pk})

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


def get_shelves_ajax_view(request):
    if request.method == "POST":
        return logic.get_shelves_ajax(request)


def get_book_ajax_view(request):
    if request.method == "POST":
        return logic.get_book_ajax(request)


def parse_book_view(request):
    if request.method == "POST":
        return logic.parse_book(request)


def swap_favorite_view(request, **kwargs):
    logic.swap_favorite(kwargs)
    return HttpResponseRedirect(reverse('book-detail', kwargs={'pk': kwargs['pk']}))


def swap_read_view(request, **kwargs):
    logic.swap_read(kwargs)
    return HttpResponseRedirect(reverse('book-detail', kwargs={'pk': kwargs['pk']}))


def new_active_shelf_view(request, **kwargs):
    logic.new_active_shelf(user=request.user, kwargs=kwargs)
    return HttpResponseRedirect(reverse('shelf-detail', kwargs={'pk': kwargs['pk']}))
