# Generated by Django 4.0.4 on 2022-05-11 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0012_rename_user_note_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='favorite',
            field=models.BooleanField(default=False, verbose_name='Избранное'),
        ),
    ]
