# Generated by Django 2.2.19 on 2022-09-16 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_auto_20220916_1839'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='nonunique_following_constraint'),
        ),
    ]
