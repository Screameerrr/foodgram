from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from users.constants import (EMAIL_MAX_LENGTH, NAME_MAX_LENGTH,
                             PASSWORD_MAX_LENGTH)


class User(AbstractUser):
    email = models.EmailField(
        "Электронная почта", max_length=EMAIL_MAX_LENGTH, unique=True
    )
    username = models.CharField(
        "Имя пользователя",
        max_length=NAME_MAX_LENGTH,
        unique=True,
        validators=[RegexValidator(regex=r"^[\w.@+-]+\Z")],
    )
    first_name = models.CharField("Имя", max_length=NAME_MAX_LENGTH)
    last_name = models.CharField("Фамилия", max_length=NAME_MAX_LENGTH)
    password = models.CharField("Пароль", max_length=PASSWORD_MAX_LENGTH)
    avatar = models.ImageField(
        upload_to="users/", null=True, blank=True, verbose_name="Аватар"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.email}: {self.first_name} {self.last_name}"


class Subscription(models.Model):
    user = models.ForeignKey(
        User, related_name="subscriptions", on_delete=models.CASCADE
    )
    subscribed_to = models.ForeignKey(
        User,
        related_name="subscribers",
        on_delete=models.CASCADE,
        verbose_name="Подписан на",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "subscribed_to"], name="unique_subscription"
            )
        ]
