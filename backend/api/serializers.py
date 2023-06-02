from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from foodgram.settings import (MAX_AMOUNT, MAX_COOKING_TIME, MIN_AMOUNT,
                               MIN_COOKING_TIME)
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow, User


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
                user.is_authenticated
                and obj.following.filter(user=user).exists()
        )


class CustomUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password')
        required_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    ingredients = IngredientRecipeSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return obj.favorite_recipe.filter(
            user=user,
            favorite_recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return obj.in_shopping_cart.filter(
            user=user,
            recipe=obj
        ).exists()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')
        required_fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())
    )
    ingredients = IngredientInRecipeWriteSerializer(many=True, write_only=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME
    )

    class Meta:
        model = Recipe
        required_fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )
        exclude = ('pub_date',)

    def add_ingredient(self, ingredients, recipe):
        recipe.ingredients.clear()
        ingredients_list = []
        for ingredient in ingredients:
            ingredients_list.append(
                IngredientRecipe(
                    recipe=recipe,
                    amount=ingredient['amount'],
                    ingredient=ingredient['id']
                ))
        IngredientRecipe.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.add_ingredient(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        instance.save()
        self.add_ingredient(ingredients, instance)
        instance.tags.set(tags)
        return instance


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        recipe = obj
        return recipe.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredientinrecipe__amount')
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class RecipeFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.CharField(
        read_only=True,
        source='author.email'
    )
    id = serializers.IntegerField(
        read_only=True,
        source='author.id'
    )
    username = serializers.CharField(
        read_only=True,
        source='author.username'
    )
    first_name = serializers.CharField(
        read_only=True,
        source='author.first_name'
    )
    last_name = serializers.CharField(
        read_only=True,
        source='author.last_name'
    )
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, author):
        user = self.context.get('request').user
        return not user.is_anonymous and Follow.objects.filter(
            user=user, author=author.author).exists()

    def validate(self, data):
        author_id = self.context.get(
            'request').parser_context.get('kwargs').get('id')
        author = get_object_or_404(User, id=author_id)
        user = self.context.get('request').user
        if user.following.filter(author=author).exists():
            raise serializers.ValidationError(
                detail='Вы уже подписаны на этого автора!',
            )
        if user == author:
            raise serializers.ValidationError(
                detail='Невозможно подписаться на себя!',
            )
        return data

    def get_recipes(self, obj):
        queryset = obj.user.recipes.all()
        limit = self.context['request'].query_params.get('recipes_limit')
        if limit:
            try:
                limit = int(limit)
                queryset = queryset[:limit]
            except ValueError:
                pass
        serializer = RecipeFollowSerializer(queryset, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.user.recipes.count()


class FavoriteSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(
        source='favorite_recipe.name',
        read_only=True
    )
    image = serializers.ImageField(
        source='favorite_recipe.image',
        read_only=True
    )
    cooking_time = serializers.IntegerField(
        source='favorite_recipe.cooking_time',
        read_only=True
    )
    id = serializers.PrimaryKeyRelatedField(
        source='favorite_recipe.id',
        read_only=True
    )

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'coocking_time',)

    def validate(self, recipe):
        if recipe.favorite_recipe.exists():
            raise serializers.ValidationError(
                'Рецепт уже в избранном!'
            )
        return recipe


class ShoppingCartSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        source='recipe.name',
        read_only=True
    )
    image = serializers.ImageField(
        source='recipe.image',
        read_only=True
    )
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True
    )
    id = serializers.PrimaryKeyRelatedField(
        source='recipe.id',
        read_only=True
    )

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'coocking_time')

    def validate(self, recipe):
        if recipe.in_shopping_cart.exists():
            raise serializers.ValidationError(
                'Ингредиент уже в списке покупок!'
            )
        return recipe
