from django.core.exceptions import ValidationError

from users.constants import FORBIDDEN_USERNAME


def validate_username_not_me(value):
    """
    Запрещает использование конкретного имени пользователя.
    """
    if value == FORBIDDEN_USERNAME:
        raise ValidationError(
            f"Нельзя использовать '{FORBIDDEN_USERNAME}' в качестве "
            "имени пользователя."
        )
