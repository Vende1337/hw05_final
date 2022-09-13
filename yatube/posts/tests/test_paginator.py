import math

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.conf import settings
from django.urls import reverse

from ..models import Post, Group


User = get_user_model()


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовый текст',
            slug='test-slug',
        )
        cls.POST_COUNT = 14
        cls.PAGE_COUNT = math.ceil(cls.POST_COUNT / settings.POSTS_PER_PAGE)
        Post.objects.bulk_create(
            Post(text=f'Пост №{index}', author=cls.user,
                 group_id=cls.group.id, id=index)
            for index in range(cls.POST_COUNT))
        cls.responses = [
            (reverse('posts:index_path')),
            (reverse('posts:group_list', kwargs={'slug': cls.group.slug})),
            (reverse('posts:profile', kwargs={'username': cls.user.username})),
        ]

    def setUp(self):
        self.author_post = Client()
        self.author_post.force_login(self.user)

    def test_first_page_paginator(self):
        for address in self.responses:
            with self.subTest(address=address):
                response = self.author_post.get(address)
                self.assertEqual(
                    len(response.context['page_obj']), settings.POSTS_PER_PAGE)

    def test_last_page_paginator(self):
        for address in self.responses:
            with self.subTest(address=address):
                response = self.author_post.get(
                    address + f'?page={self.PAGE_COUNT}')
                self.assertEqual(
                    len(response.context['page_obj']),
                    (self.POST_COUNT
                     - (settings.POSTS_PER_PAGE
                        * (self.PAGE_COUNT) - settings.POSTS_PER_PAGE)))
