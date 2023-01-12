import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='IvanTest')
        cls.group_test = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Описание тестовой группы'
        )
        cls.page_list = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group_test.slug}),
            reverse('posts:profile', kwargs={'username': cls.user.username})
        }
        post_list = []
        for i in range(0, settings.POSTS_ON_PAGE + 3):
            new_post = Post(
                text=f'Тестовый пост контент {i}',
                group=cls.group_test,
                author=cls.user
            )
            post_list.append(new_post)
        Post.objects.bulk_create(post_list)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Проверка первой страницы пагинатора."""
        for page in self.page_list:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    len(response.context.get('page_obj')),
                    settings.POSTS_ON_PAGE
                )

    def test_second_page_contains_three_records(self):
        """Проверка второй страницы пагинатора."""
        count_posts = Post.objects.count() - settings.POSTS_ON_PAGE
        for page in self.page_list:
            with self.subTest(page=page):
                response = self.authorized_client.get(page + '?page=2')
                self.assertEqual(
                    len(response.context.get('page_obj')), count_posts
                )


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_test = Group.objects.create(
            title='test',
            slug='test',
            description='Текстовое описание группы'
        )
        cls.user = User.objects.create(username='IvanTest')
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif",
            content=cls.small_gif,
            content_type="image/gif"
        )
        cls.post_test = Post.objects.create(
            text='Тестовый пост контент',
            group=cls.group_test,
            author=cls.user,
            image=cls.uploaded
        )
        cls.author = User.objects.create(username='author')
        cls.index_url = reverse('posts:index')
        cls.group_list = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group_test.slug}
        )
        cls.profile = reverse(
            'posts:profile',
            kwargs={'username': cls.post_test.author}
        )
        cls.post_detail_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post_test.pk}
        )
        cls.post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post_test.pk}
        )
        cls.post_create_url = reverse('posts:post_create')
        cls.urls = [
            (cls.index_url, 'posts/index.html'),
            (cls.group_list, 'posts/group_list.html'),
            (cls.profile, 'posts/profile.html'),
            (cls.post_detail_url, 'posts/post_detail.html'),
            (cls.post_edit_url, 'posts/create_post.html'),
            (cls.post_create_url, 'posts/create_post.html'),
        ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    # тот самый метод, который начинается не с test_**
    def check_post_info(self, context, page=True):
        if page:
            page_obj = context.get('page_obj')
            self.assertIsInstance(page_obj, Page, 'хотели Page')
            post = page_obj[0]
        else:
            post = context.get('post')
        self.assertIsInstance(self.post_test, Post)
        self.assertEqual(post.text, self.post_test.text)
        self.assertEqual(post.author, self.post_test.author)
        self.assertEqual(post.group, self.post_test.group)
        self.assertEqual(post.image, self.post_test.image)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for adress, template in self.urls:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Проверка контекста index."""
        response = self.authorized_client.get(self.index_url)
        self.check_post_info(response.context)

    def test_group_list_show_correct_context(self):
        """Проверка контекста group_list."""
        response = self.authorized_client.get(self.group_list)
        context_group = response.context.get('group')
        self.assertEqual(context_group, self.group_test)
        self.check_post_info(response.context)

    def test_profile_show_correct_context(self):
        """Проверка контекста profile."""
        response = self.authorized_client.get(self.profile)
        context_author = response.context.get('author')
        self.assertEqual(context_author, self.user)
        self.check_post_info(response.context)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.post_create_url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                Post.objects.filter(
                    author_id=self.user.pk
                )[:settings.POSTS_ON_PAGE]
                param = response.context.get('form')
                self.assertIsInstance(param, PostForm)
                form_field = param.fields.get(value)
                self.assertTrue('is_edit', response.context)
                self.assertIsInstance(form_field, expected)

    def test_create_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.post_edit_url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                Post.objects.filter(
                    author_id=self.user.id
                )[:settings.POSTS_ON_PAGE]
                param = response.context.get('form')
                self.assertIsInstance(param, PostForm)
                form_field = param.fields.get(value)
                self.assertTrue('is_edit', response.context)
                self.assertIsInstance(form_field, expected)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(self.post_detail_url)
        self.check_post_info(response.context, False)

    def test_check_group_in_pages(self):
        """Проверка, что Пост создан на странице с выбранной группой"""
        post_new = Post.objects.create(
            text='Тестовый пост контент',
            group=self.group_test,
            author=self.user,
        )
        urls_lists = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group_test.slug}),
            reverse('posts:profile', kwargs={'username': post_new.author})
        }
        for value in urls_lists:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                urls_lists = response.context.get('page_obj')

    def test_check_group_not_in_mistake_group_list_page(self):
        """Проверка, что созданный Пост попап в свою группу."""
        group_new = Group.objects.create(
            title='Очередная тестова группа',
            slug='test_slug_two')
        post_new = Post.objects.create(
            text='Очередной текст',
            group=self.group_test,
            author=self.user,
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': group_new.slug}))
        self.assertEqual(len(response.context.get('page_obj')), 0)
        context_post = response.context.get('page_obj')
        self.assertNotIn(post_new, context_post)

    def test_cache_index(self):
        """Проверяем, что главная отдает кэшированные данные."""
        post = Post.objects.create(
            text='Пост под кеш',
            author=self.author)
        content_add = self.author_client.get(
            reverse('posts:index')).content
        post.delete()
        content_delete = self.author_client.get(
            reverse('posts:index')).content
        self.assertEqual(content_add, content_delete)
        cache.clear()
        content_cache_clear = self.author_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(content_add, content_cache_clear)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super(FollowTests, cls).setUpClass()
        cls.user = User.objects.create(username='IvanTest')
        cls.author = User.objects.create(username='author')
        cls.follower = User.objects.create(username='Podpishik')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Описание тестовой группы'
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif",
            content=cls.small_gif,
            content_type="image/gif"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.guest_client = Client()
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_follow_on_user(self):
        """Проверяем что подписка работает."""
        count_follow = Follow.objects.count()
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )
        )
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.author.id)
        self.assertEqual(follow.user_id, self.follower.id)

    def test_unfollow_on_user(self):
        """Проверяем что отписка работает."""
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        count_follow = Follow.objects.count()
        self.follower_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_follow_on_authors(self):
        """Проверяем записи избранных авторов."""
        post = Post.objects.create(
            author=self.author,
            text='Подпишись на меня'
        )
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        response = self.follower_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        self.assertIn(post, response.context.get('page_obj').object_list)

    def test_notfollow_on_authors(self):
        """Проверяем записи у не избранных авторов"""
        post = Post.objects.create(
            author=self.author,
            text='Подпишись на меня'
        )
        response = self.follower_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(post, response.context.get('page_obj').object_list)
