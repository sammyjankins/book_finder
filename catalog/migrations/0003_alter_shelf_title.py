# Generated by Django 4.0.4 on 2022-05-08 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_alter_book_bookcase_alter_book_shelf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shelf',
            name='title',
            field=models.CharField(max_length=100, unique=True, verbose_name='Название'),
        ),
    ]