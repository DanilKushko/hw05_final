from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, длиной более 15 символов',
        )

    def test_models_have_correct_object_names_for_group(self):
        """У модели group корректно работает __str__."""
        models = {
            self.group.title: self.group,
        }
        for model_str, model in models.items():
            with self.subTest(model=model):
                self.assertEqual(model_str, str(model))

    def test_models_have_correct_object_names_for_post(self):
        """У модели post корректно работает __str__."""
        models = {
            self.post.text[:15]: self.post
        }
        for model_str, model in models.items():
            with self.subTest(model=model):
                self.assertEqual(model_str, str(model))
