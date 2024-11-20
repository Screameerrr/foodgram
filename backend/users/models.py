from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from users.constants import (
    MAX_LENGTH_FIRST_NAME,
    MAX_LENGTH_LAST_NAME,
)


def validate_username_not_me(value):
    """Запрещает использование имени 'me' в качестве имени пользователя."""
    if value.lower() == 'me':
        raise ValidationError(
            "Нельзя использовать 'me' в качестве имени пользователя."
        )


class User(AbstractUser):
    """Пользователь."""

    email = models.EmailField(
        verbose_name='адрес электронной почты',
        unique=True,
        error_messages={
            'unique': (
                "Пользователь с таким адресом электронной почты существует."
            ),
        },
    )
    username = models.CharField(
        verbose_name='имя пользователя',
        max_length=150,
        unique=True,
        help_text=(
            'Обязательное поле. Не более 150 символов. Только буквы, цифры и '
            '@/./+/-/_ .'
        ),
        validators=[validate_username_not_me],
        error_messages={
            'unique': (
                "Пользователь с таким именем уже существует."
            ),
        },
    )
    first_name = models.CharField(
        verbose_name='имя',
        max_length=MAX_LENGTH_FIRST_NAME,
    )
    last_name = models.CharField(
        verbose_name='фамилия',
        max_length=MAX_LENGTH_LAST_NAME,
    )
    avatar = models.ImageField(
        verbose_name='аватар',
        upload_to='user/',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        ordering = ['first_name']

    def __str__(self):
        return self.username


class Subscriber(models.Model):
    """Подписка."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='автор',
    )
    created_at = models.DateTimeField(
        verbose_name='дата подписки',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscriber',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='unique_subscriber_himself',
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} подписан на {self.author.username}"
        )

    @classmethod
    def get_prefetch_subscribers(cls, lookup, user):
        return models.Prefetch(
            lookup,
            queryset=cls.objects.all().annotate(
                is_subscribed=models.Exists(
                    cls.objects.filter(
                        author=models.OuterRef('author'),
                        user_id=user.id,
                    )
                )
            ),
            to_attr='subs',
        )
