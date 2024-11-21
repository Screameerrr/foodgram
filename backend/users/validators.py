from django.core.exceptions import ValidationError

from users.constants import FORBIDDEN_USERNAME


def validate_username_forbidden(value):
    """
    Проверяет, запрещено ли использование указанного имени пользователя.
    """
    if value == FORBIDDEN_USERNAME:
        raise ValidationError(
            f"Нельзя использовать '{FORBIDDEN_USERNAME}' в качестве"
            f"имени пользователя."
        )
