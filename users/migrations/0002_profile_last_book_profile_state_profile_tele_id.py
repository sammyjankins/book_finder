# Generated by Django 4.0.4 on 2022-05-12 17:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0015_alter_book_new_author'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='last_book',
            field=models.ForeignKey(default='', null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalog.book', verbose_name='Последняя книга'),
        ),
        migrations.AddField(
            model_name='profile',
            name='state',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='profile',
            name='tele_id',
            field=models.CharField(default='', max_length=15),
        ),
    ]
