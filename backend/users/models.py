from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.constants import MAX_LENGTH_FIRST_NAME, MAX_LENGTH_LAST_NAME

class User(AbstractUser):
    """Пользователь."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(
        _("first name"),
        max_length=MAX_LENGTH_FIRST_NAME
    )
    last_name = models.CharField(
        _("last name"),
        max_length=MAX_LENGTH_LAST_NAME
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='user/',
        blank=True, null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        ordering = ['id']




class Subscriber(models.Model):
    """Подписки."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers'
    )
    created_at = models.DateTimeField(
        'Дата подписки',
        auto_now_add=True
    )

    class Meta:
        default_related_name = 'subscribers'
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscriber'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='unique_subscriber_himself',
            ),
        ]

    def __str__(self):
        return f'{self.user.username!r} подписан на {self.author.username!r}'

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
