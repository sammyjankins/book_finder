from PIL import Image
from django.db import models
from django.contrib.auth.models import User

from catalog.models import Book


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    tele_id = models.CharField(max_length=15, default='', unique=True)
    last_book = models.ForeignKey(Book, verbose_name='Последняя книга', on_delete=models.SET_NULL, null=True,
                                  default='')
    state = models.IntegerField(default=0)

    def __str__(self):
        return f'Профиль {self.user.username}'

    def save(self, **kwargs):
        super().save()

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)

    def set_dialog_state(self, state):
        self.state = state
        self.save()

