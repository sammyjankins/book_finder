# Generated by Django 4.0.4 on 2022-05-09 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007_alter_book_new_author'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='name',
            field=models.CharField(max_length=150, verbose_name='Имя'),
        ),
    ]