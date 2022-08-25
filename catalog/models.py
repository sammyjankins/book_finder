from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import CharField
from django.db.models.functions import Lower

CharField.register_lookup(Lower)


class BookCase(models.Model):
    title = models.CharField(verbose_name='Название', max_length=100)
    shelf_count = models.IntegerField(verbose_name='Количество полок', default=1)
    section_count = models.IntegerField(verbose_name='Количество секций', default=1)
    row_count = models.IntegerField(verbose_name='Количество рядов', default=1)

    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('bookcase-detail', kwargs={'pk': self.pk})

    def get_book_count(self):
        books = 0
        for shelf in self.shelves.all():
            books += shelf.book_set.all().count()
        return books


class Shelf(models.Model):
    title = models.CharField(verbose_name='Название', max_length=100)
    ROWS = (
        ('Первый', 'Первый'),
        ('Второй', 'Второй'),
        ('Третий', 'Третий'),
        ('Четвертый', 'Четвертый'),
    )
    row = models.CharField(verbose_name='Ряд', max_length=100, choices=ROWS, default='')
    bookcase = models.ForeignKey(BookCase, verbose_name='Книжный шкаф', on_delete=models.CASCADE,
                                 related_name='shelves')
    is_current = models.BooleanField(verbose_name="Является текущей", default=False)

    owner = models.ForeignKey('auth.User', related_name='shelves', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.title.lower()}, {self.row.lower()} ряд'

    def get_absolute_url(self):
        return reverse('shelf-detail', kwargs={'pk': self.pk})

    def get_current_shelf(self):
        return Shelf.objects.filter(is_current=True, owner=self.owner).first()


class Author(models.Model):
    name = models.CharField(verbose_name='Имя', max_length=150)
    date_of_birth = models.CharField(verbose_name='Дата рождения', max_length=15, default='', blank=True)
    country = models.CharField(verbose_name='Страна', max_length=100, default='', blank=True)

    owner = models.ForeignKey('auth.User', related_name='authors', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('author-detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Автор"


class Book(models.Model):
    title = models.CharField(verbose_name='Название', max_length=150)
    pages = models.IntegerField(verbose_name='Количество страниц', default='', blank=True, null=True, )
    year_of_publication = models.CharField(verbose_name='Год издания', max_length=10, default='', blank=True)
    language = models.CharField(verbose_name='Язык', max_length=50, default='', blank=True)
    ISBN = models.CharField(verbose_name='ISBN', max_length=100, default='', blank=True, null=True, )
    type_of_cover = models.CharField(verbose_name='Тип обложки', max_length=25, default='', blank=True)
    read = models.BooleanField(verbose_name='Прочитана', default=False)
    annotation = models.TextField(verbose_name='Аннотация', default='', blank=True, null=True, )

    shelf = models.ForeignKey(Shelf, verbose_name='Полка', on_delete=models.CASCADE, )
    author = models.ForeignKey(Author, verbose_name='Автор', on_delete=models.CASCADE, )
    new_author = models.CharField(verbose_name='Новый автор', max_length=150, null=True, blank=True)
    favorite = models.BooleanField(verbose_name='Избранное', default=False)

    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('book-detail', kwargs={'pk': self.pk})


class Note(models.Model):
    text = models.TextField(default='', blank=True)
    book = models.ForeignKey(Book, verbose_name='Книга', on_delete=models.CASCADE, )
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('book-detail', kwargs={'pk': self.book.pk})
