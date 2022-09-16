# Generated by Django 2.2.19 on 2022-09-16 15:39

from django.db import migrations, models
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_follow'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.CheckConstraint(check=models.Q(_negated=True, user=django.db.models.expressions.F('author')), name='user_cannot_follow_yourself'),
        ),
    ]