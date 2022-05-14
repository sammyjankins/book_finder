from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

urlpatterns = [
    path('', login_required(views.BookcaseListView.as_view()), name='bookcase-list'),
    path('book/all/', login_required(views.BookListView.as_view()), name='book-list'),
    path('author/all/', login_required(views.AuthorListView.as_view()), name='author-list'),
    path('search/', login_required(views.SearchListView.as_view()), name="search-list"),
    path('favorite/', login_required(views.FavoriteListView.as_view()), name="favorite-list"),
    path('read/', login_required(views.ReadListView.as_view()), name="read-list"),
    path('unread/', login_required(views.UnreadListView.as_view()), name="unread-list"),

    path('bookcase/<int:pk>/', login_required(views.BookcaseDetailView.as_view()), name='bookcase-detail'),
    path('author/<int:pk>/', login_required(views.AuthorDetailView.as_view()), name='author-detail'),
    path('shelf/<int:pk>/', login_required(views.ShelfDetailView.as_view()), name='shelf-detail'),
    path('book/<int:pk>/', login_required(views.BookDetailView.as_view()), name='book-detail'),

    path('bookcase/<int:pk>/update/', login_required(views.BookcaseUpdateView.as_view()), name='bookcase-update'),
    path('shelf/<int:pk>/update/', login_required(views.ShelfUpdateView.as_view()), name='shelf-update'),
    path('author/<int:pk>/update/', login_required(views.AuthorUpdateView.as_view()), name='author-update'),
    path('book/<int:pk>/update/', login_required(views.BookUpdateView.as_view()), name='book-update'),
    path('note/<int:pk>/update', login_required(views.NoteUpdateView.as_view()), name='note-update'),

    path('bookcase/<int:pk>/delete/', login_required(views.BookcaseDeleteView.as_view()), name='bookcase-delete'),
    path('author/<int:pk>/delete/', login_required(views.AuthorDeleteView.as_view()), name='author-delete'),
    path('book/<int:pk>/delete/', login_required(views.BookDeleteView.as_view()), name='book-delete'),
    path('book/<int:pk>/note/delete/', login_required(views.NoteDeleteView.as_view()), name='note-delete'),

    path('bookcase/new/', login_required(views.BookcaseCreateView.as_view()), name='bookcase-create'),
    path('author/new/', login_required(views.AuthorCreateView.as_view()), name='author-create'),
    path('book/new/', login_required(views.BookCreateView.as_view()), name='book-create'),
    path('book/<int:pk>/note/', login_required(views.NoteCreateView.as_view()), name='note-create'),

    path('get-topics-ajax/', views.get_shelves_ajax_view, name="get-shelves-ajax"),
    path('get-book-ajax/', views.get_book_ajax_view, name="get-book-ajax"),
    path('parse-book/', views.parse_book_view, name="parse-book"),
    path('swap-favorite/<int:pk>', views.swap_favorite_view, name="swap-favorite"),
    path('swap-read/<int:pk>', views.swap_read_view, name="swap-read"),
    path('new-active-shelf/<int:pk>', views.new_active_shelf_view, name="new-active-shelf"),
]
