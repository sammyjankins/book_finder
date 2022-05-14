from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from users.models import Profile
from .models import BookCase, Book, Author
from .services import create_shelves


@receiver(signal=post_save, sender=BookCase)
def create_bookcase(sender, instance, created, **kwargs):
    if created:
        create_shelves(bookcase=instance)


@receiver(signal=post_save, sender=Book)
def create_bookcase(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.get(user=instance.owner)
        profile.last_book = instance
        profile.save()
