from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200, verbose_name='Название',
        help_text='Укажите название группы'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Slug',
        help_text='Укажите Slug группы'
    )
    description = models.TextField(
        max_length=400, verbose_name='Описание',
        help_text='Укажите описание группы'
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    LEN_POST: int = 15

    text = models.TextField(verbose_name='Текст',
                            help_text='Напишите текст поста')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
        help_text='Укажите дату публикации поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор поста',
        help_text='Укажите автора поста',
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Группа поста',
        help_text='Укажите группу поста',
        related_name='posts'
    )

    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:self.LEN_POST]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария',
        help_text='Укажите автора комментария',
        related_name='comments'
    )
    text = models.TextField(verbose_name='Текст',
                            help_text='Напишите текст комментария')
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
        help_text='Укажите дату публикации комментария')


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following')

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='user_cannot_follow_yourself'
            ),
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='nonunique_following_constraint'
            )
        ]
