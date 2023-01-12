from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Comment, Group, Post

User = get_user_model()


class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='IvanTest')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_form_create(self):
        """Валидная форма создает запись в Post."""
        self.group_one = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        post_count = Post.objects.count()
        form_data = {
            'group': self.group_one.pk,
            'text': 'Тестеровщик чуть не умер!!!',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text']).exists()
        )

    def test_post_creat_without_group(self):
        """Валидная форма создает запись в Post без группы"""
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый текст без группы',
        )
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестеровщик чуть не умер!!!',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data.get('text')).exists()
        )

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый текст',
        )
        self.group_two = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Устал, Босс!',
            'group': self.group_two.id,
            'image': b"\x47\x49\x46\x38\x39\x61\x02\x00"
                     b"\x01\x00\x80\x00\x00\x00\x00\x00"
                     b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
                     b"\x00\x00\x00\x2C\x00\x00\x00\x00"
                     b"\x02\x00\x01\x00\x00\x02\x02\x0C"
                     b"\x0A\x00\x3B",
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=({self.post.pk})),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data.get('text')
            ).exists()
        )


class ComentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='IvanTest')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Описание тестовой группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            group=cls.group,
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post,
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()
        cache.clear()

    def test_comment_push(self):
        """Проверка, что комментарий создан."""
        self.post = Post.objects.create(
            text='Тестовый пост',
            group=self.group,
            author=self.user,
        )
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            )
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(text='Тестовый комментарий').exists()
        )

    def test_guest_comment_cant(self):
        """Проверка, что гостевой пользователь не может добавить
        комментарий.
        """
        self.post = Post.objects.create(
            text='Тестовый пост',
            group=self.group,
            author=self.user,
        )
        form_data = {
            'text': 'Снова тестовый комментарий',
            'post': self.post.pk
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'post_id': self.post.pk
                }
            ),
            data=form_data
        )
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data
        )
        # комментарий был создан уже в предыдущем тесте, поэтому 1=1
        # я так понял)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertRedirects(
            response,
            '/auth/login/?next=/posts/2/comment/'
        )
