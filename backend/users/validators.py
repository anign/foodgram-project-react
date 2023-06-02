import re

from django.core.exceptions import ValidationError

from foodgram.settings import FORBIDDEN_NAMES


def validate_username(value):
    if value == FORBIDDEN_NAMES:
        raise ValidationError(
            'Имена пользователей {FORBIDDEN_NAMES} запрещены!'
        )
    forbidden_symbols = "".join(set(re.sub(r"[\w.@+-]+", "", value)))
    if forbidden_symbols:
        raise ValidationError(
            f'Имя пользователя содержит недопустимые символы:'
            f'{forbidden_symbols}'
        )
    return value
