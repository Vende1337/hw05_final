import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Post, Group, Follow
from ..forms import PostForm


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif')

        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовый текст',
            slug='test-slug',
        )
        cls.false_group = Group.objects.create(
            title='Тестовая группа_2',
            description='Тестовый текст_2',
            slug='test2-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )
        cls.responses = [
            (reverse('posts:index_path'), True),
            ((reverse('posts:group_list',
             kwargs={'slug': cls.group.slug})), True),
            ((reverse('posts:profile',
             kwargs={'username': cls.user.username})), True),
            ((reverse('posts:post_detail',
             kwargs={'post_id': cls.post.id})), False),
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_post = Client()
        self.author_post.force_login(self.user)

    def test_correct_context(self):
        for (address, contain_page_obj) in self.responses:
            with self.subTest(address=address):
                response = self.author_post.get(address)
                if not contain_page_obj:
                    first_object = response.context['post']
                else:
                    first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.text, self.post.text)
                self.assertEqual(first_object.author, self.post.author)
                self.assertEqual(first_object.pk, self.post.id)
                self.assertEqual(first_object, self.post)
                self.assertEqual(first_object.image, self.post.image)

    def test_correct_group(self):
        response = self.author_post.get((reverse(
            'posts:group_list',
            kwargs={'slug': self.false_group.slug})))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_group_context(self):
        response = self.author_post.get((reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug})))
        group_object = response.context['group']
        self.assertEqual(group_object.title, self.group.title)
        self.assertEqual(group_object.description, self.group.description)
        self.assertEqual(group_object.slug, self.group.slug)

    def test_profile_context(self):
        response = self.author_post.get((reverse(
            'posts:profile',
            kwargs={'username': self.user.username})))
        profile_object = response.context['author']
        self.assertEqual(profile_object.username, self.user.username)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_post.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['form'].instance, self.post)
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.author_post.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.author_post = Client()
        cls.author_post.force_login(cls.user)

    def test_cache_index(self):
        cache.clear()
        post = Post.objects.create(
            author=self.user,
            text='Тестовый текст',
        )
        response_first = self.author_post.get(reverse('posts:index_path'))
        self.assertIn(post.text, response_first.content.decode())
        post.delete()
        response_second = self.author_post.get(reverse('posts:index_path'))
        self.assertIn(post.text, response_second.content.decode())
        cache.clear()
        response_third = self.author_post.get(reverse('posts:index_path'))
        self.assertNotIn(post.text, response_third.content.decode())


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_first = User.objects.create_user(username='author')
        cls.user_second = User.objects.create_user(username='vasia')
        cls.user_third = User.objects.create_user(username='sasha')

    def setUp(self):
        self.author_post = Client()
        self.author_post.force_login(self.user_first)
        self.follower_cleint = Client()
        self.follower_cleint.force_login(self.user_second)
        self.follower_second_cleint = Client()
        self.follower_second_cleint.force_login(self.user_third)

    def test_follow_unfollow(self):
        self.author_post.get(reverse('posts:profile_follow', kwargs={
                             'username': self.user_second}))
        self.assertTrue(Follow.objects.filter(
            user=self.user_first, author=self.user_second).exists())
        self.author_post.get(reverse('posts:profile_unfollow', kwargs={
                             'username': self.user_second}))
        self.assertFalse(Follow.objects.filter(
            user=self.user_first, author=self.user_second).exists())

    def test_follow_page(self):
        self.author_post.get(reverse('posts:profile_follow', kwargs={
                             'username': self.user_second}))
        post = Post.objects.create(
            author=self.user_second,
            text='Тестовый текст',
        )
        response = self.author_post.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'])
        response_second = self.follower_second_cleint.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response_second.context['page_obj'])
