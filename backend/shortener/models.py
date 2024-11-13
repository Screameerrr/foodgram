import string
from random import choice, randint

from django.db import models

from shortener.constants import (
    MIN,
    MAX,
    MAX_HASH,
    URL
)


def generate_hash() -> str:
    """Генератор."""

    return ''.join(
        choice(string.ascii_letters + string.digits)
        for _ in range(randint(MIN, MAX))
    )


class LinkMapped(models.Model):
    """Ссылки."""

    url_hash = models.CharField(
        'Короткая ссылка',
        max_length=MAX_HASH,
        default=generate_hash,
        unique=True
    )
    original_url = models.URLField(
        'Оригинальная ссылка',
        max_length=URL
    )

    class Meta:
        verbose_name = 'Ссылка'
        verbose_name_plural = 'Ссылки'

    def __str__(self):
        return f'{self.original_url} -> {self.url_hash}'
