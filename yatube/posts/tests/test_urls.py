from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_user = User.objects.create_user(username='NonAuthor')
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.responses = [
            ((reverse('posts:index_path')), 'posts/index.html', 200, False),
            ((reverse('posts:group_list',
             kwargs={'slug': cls.group.slug})), 'posts/group_list.html',
             200, False),
            ((reverse('posts:profile',
             kwargs={'username': cls.user.username})), 'posts/profile.html/',
             200, False),
            ((reverse('posts:post_detail',
             kwargs={'post_id': cls.post.id})), 'posts/post_detail.html',
             200, False),
            ((reverse('posts:post_edit', kwargs={
             'post_id': cls.post.id})), 'posts/create_post.html', 200, True),
            ((reverse('posts:post_create')), 'posts/create_post.html',
             200, True),
            ('/unexpected_page/', 'core/404.html', 404, False),
        ]

    def setUp(self):
        self.guest_client = Client()
        self.author_post = Client()
        self.author_post.force_login(self.user)

    def test_template_url(self):
        for (address, template, status,
             is_authotizated) in self.responses:
            with self.subTest(address=address):
                if template is not None:
                    response = self.author_post.get(address)
                    self.assertTemplateUsed(response, template)

    def test_status_code(self):
        for (address, template, status,
             is_authotizated) in self.responses:
            with self.subTest(address=address):
                if not is_authotizated:
                    response = self.guest_client.get(address)
                elif is_authotizated:
                    response = self.author_post.get(address)
                self.assertEqual(response.status_code, status)

    def test_redirect_url(self):
        responses_redirect = [
            ((reverse('posts:post_edit', kwargs={
             'post_id': self.post.id})), True, True),
            ((reverse('posts:post_create')), True, False),

        ]

        for (address, for_guest, for_non_author) in responses_redirect:
            with self.subTest(address=address):
                if for_guest:
                    response = self.guest_client.get(address)
                    self.assertRedirects(
                        response, (reverse('users:login'))
                        + f'?next={address}')
                elif for_non_author:
                    response = self.author_post.force_login(
                        self.authorized_user).get(address)
                    self.assertRedirects(response, (f'/posts/{self.post.id}/'))

    def test_reverse_url(self):
        reverse_url = [
            ((reverse('posts:index_path')), '/'),
            ((reverse('posts:group_list',
             kwargs={'slug': self.group.slug})), f'/group/{self.group.slug}/'),
            ((reverse('posts:profile',
             kwargs={'username': self.user.username})),
             f'/profile/{self.user.username}/'),
            ((reverse('posts:post_detail',
             kwargs={'post_id': self.post.id})), f'/posts/{self.post.id}/'),
            ((reverse('posts:post_edit', kwargs={
             'post_id': self.post.id})), f'/posts/{self.post.id}/edit/'),
            ((reverse('posts:post_create')), '/create/'),
        ]

        for (revers, address) in reverse_url:
            with self.subTest(address=address):
                self.assertEqual(revers, address)
