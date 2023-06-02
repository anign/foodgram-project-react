from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Электронная почта',
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        related_name='subscriber',
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        related_name='subscribing',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
