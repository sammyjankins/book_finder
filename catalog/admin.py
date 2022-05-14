from django.contrib import admin
from .models import BookCase, Author, Book

admin.site.register([BookCase, Author, Book])
