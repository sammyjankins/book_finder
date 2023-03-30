from django.contrib import admin
from .models import BookCase, Author, Book, Shelf

admin.site.register([BookCase, Author, Book, Shelf])
