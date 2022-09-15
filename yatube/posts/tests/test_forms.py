import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse


from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from ..models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовый текст',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст2',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def check_object(self, post_object, author, text, group):
        with self.subTest(post_object=post_object):
            self.assertEqual(post_object.author, author)
            self.assertEqual(post_object.text, text)
            self.assertEqual(post_object.group_id, group)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Провреяем что форма создания поста рабоатет правильно"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')

        posts_before_form = set(Post.objects.values_list('id', flat=True))
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        posts_after_form = set(Post.objects.values_list('id', flat=True))
        posts_count = posts_after_form - posts_before_form
        self.assertEqual(len(posts_count), 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user}))
        post_object = Post.objects.get(id=posts_count.pop())
        self.check_object(post_object, self.user,
                          form_data['text'], form_data['group'],)
        self.assertEqual(post_object.image, 'posts/small.gif')

    def test_edit_form(self):
        """Провреяем что форма редактирования поста рабоатет правильно"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст',
            'group': self.group.id
        }
        response = self.authorized_client.post(reverse('posts:post_edit',
                                               kwargs={'post_id':
                                                       self.post.id}),
                                               data=form_data,
                                               follow=True)
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id':
                                                       self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        post_object = Post.objects.get(id=self.post.id)
        self.check_object(post_object, self.post.author,
                          form_data['text'], form_data['group'],)

    def test_comment_form_guest(self):
        comment_count_before_form = self.post.comments.all().count()
        form_data = {
            'text': 'Текст комментария'
        }
        self.guest_client.post(reverse('posts:add_comment',
                                       kwargs={'post_id':
                                               self.post.id}),
                               data=form_data,
                               follow=True)
        comment_count_after_form = self.post.comments.all().count()

        self.assertEqual(comment_count_after_form
                         - comment_count_before_form, 0)

    def test_comment_form_authorizated(self):

        comment_before_form = set(Comment.objects.values_list('id', flat=True))
        form_data = {
            'text': 'Текст комментария'
        }
        self.authorized_client.post(reverse('posts:add_comment',
                                            kwargs={'post_id':
                                                    self.post.id}),
                                    data=form_data,
                                    follow=True)
        comment_after_form = set(Comment.objects.values_list('id', flat=True))
        comment_count = comment_after_form - comment_before_form
        self.assertEqual(len(comment_count), 1)
        comment_object = Comment.objects.get(id=comment_count.pop())
        self.assertEqual(comment_object.text, form_data['text'])
        self.assertEqual(comment_object.author, self.user)
        self.assertEqual(comment_object.post_id, self.post.id)
