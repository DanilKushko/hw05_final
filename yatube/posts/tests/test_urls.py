from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='IvanTest')
        cls.group_test = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Текстовое описание группы'
        )
        cls.post_test = Post.objects.create(
            text='Тестовый пост контент',
            group=cls.group_test,
            author=cls.user,
        )
        cls.pages_for_all = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{cls.group_test.slug}/',
            'posts/profile.html': f'/profile/{cls.user.username}/',
            'posts/post_detail.html': f'/posts/{cls.post_test.pk}/',
        }
        cls.pages_for_client = {
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post_test.pk}/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_pages(self):
        """Проверка доступности публичных страниц приложения posts."""
        for template, reverse_name in self.pages_for_all.items():
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_private_pages(self):
        """Проверка доступности страниц приложения posts
        для авторизованного пользователя.
        """
        for reverse_name, template in self.pages_for_client.items():
            with self.subTest():
                response = self.authorized_client.get(
                    reverse_name,
                    follow=False
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_anonim_private_pages(self):
        """Проверка доступности страниц приложения posts
        для не авторизованного пользователя.
        """
        for reverse_name, template in self.pages_for_client.items():
            with self.subTest():
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_wrong_uri_returns_404(self):
        """Проверка 404 страницы."""
        response = self.client.get('/posts/test404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_reddirect_guest_client(self):
        """Проверка редиректа неавторизованного пользователя"""
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group_test,
        )
        form_data = {
            'text': 'Текст, текст и снова текст!'
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.pk}/edit/'
        )

    def test_reddirect_authorized_client(self):
        """Проверка редиректа авторизованного пользователя"""
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group_test,
        )
        form_data = {
            'text': 'Текст, текст и снова текст!'
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            f'/posts/{self.post.pk}/'
        )
