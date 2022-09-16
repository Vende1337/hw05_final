# Generated by Django 2.2.19 on 2022-09-16 16:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_auto_20220916_1841'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='author',
            field=models.ForeignKey(help_text='Укажите автора поста', on_delete=django.db.models.deletion.CASCADE, related_name='author', to=settings.AUTH_USER_MODEL, verbose_name='Автор поста'),
        ),
        migrations.AlterField(
            model_name='post',
            name='group',
            field=models.ForeignKey(blank=True, help_text='Укажите группу поста', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='group', to='posts.Group', verbose_name='Группа поста'),
        ),
    ]
