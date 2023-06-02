from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import UniqueConstraint


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='��������'
    )
    color = models.CharField(
        max_length=7,
        unique=True,
        verbose_name='HEX-���',
        validators=[
            RegexValidator(
                regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                message='��������� �������� �� �������� ������ � ������� HEX!'
            )
        ]
    )
    slug = models.SlugField(
        unique=True,
        max_length=200,
        verbose_name='���������� �������������'
    )

    class Meta:
        verbose_name = '���'
        verbose_name_plural = '����'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='��������'
    )
    measurement_unit = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='������� ���������'
    )

    class Meta:
        verbose_name = '����������'
        verbose_name_plural = '�����������'
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    name = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='�������� �������',
    )
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        null=True,
        verbose_name='�����',
    )
    text = models.TextField(
        blank=False,
        verbose_name='�������� �������'
    )
    image = models.ImageField(
        upload_to='recipes/image/',
        blank=False,
        verbose_name='���� �����'
    )
    cooking_time = models.PositiveIntegerField(
        blank=False,
        validators=[
            MinValueValidator(1, message='����������� �������� 1!')
        ],
        verbose_name='����� �������������'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='�����������'
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagInRecipe',
        related_name='recipes',
        blank=False,
        verbose_name='����'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='���� ����������'
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = '������'
        verbose_name_plural = '�������'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_list',
        verbose_name='������'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='����������',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, message='����������� ���������� 1!')
        ],
        verbose_name='����������'
    )

    class Meta:
        verbose_name = '���������� � �������'
        verbose_name_plural = '����������� � ��������'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredientrecipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class TagInRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='����',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='������',
    )

    class Meta:
        verbose_name = '���� �������'
        verbose_name_plural = '���� �������'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'],
                name='unique_tagrecipe'
            )
        ]

    def __str__(self):
        return f'{self.tag} {self.recipe}'


class Favourite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='������������',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='������',
    )

    class Meta:
        verbose_name = '���������'
        verbose_name_plural = '���������'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favourite'
            )
        ]

    def __str__(self):
        return f'{self.user} ������� "{self.recipe}" � ���������'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='������������',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='������',
    )

    class Meta:
        verbose_name = '������ �������'
        verbose_name_plural = '������ �������'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} ������� "{self.recipe}" � ������ �������'
