from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.filters import IngredientSearchFilter, RecipesFilter
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from users.models import Follow, User

from .paginators import LimitPagination
from .permissions import (CurrentUserPermission,
                          IsAuthorOrAdminOrModerOrReadOnly)
from .serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                          FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipeSerializer,
                          ShoppingCartSerializer, TagSerializer, RecipeWriteSerializer)


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthorOrAdminOrModerOrReadOnly,)
    pagination_class = LimitPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    @action(
        methods=['GET', 'PATCH'],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role, partial=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def __get_add_delete_follow(self, request, id):
        user = get_object_or_404(User, username=request.user)
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response(
                {'errors': 'Нельзя отписываться или подписываться на себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = Follow.objects.create(user=user, author=author)
            serializer = FollowSerializer(
                follow, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(Follow, user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('post',), detail=True,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id=None):
        return self.__get_add_delete_follow(request, id)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        return self.__get_add_delete_follow(request, id)

    @action(methods=('get',), detail=False,
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthorOrAdminOrModerOrReadOnly,)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthorOrAdminOrModerOrReadOnly,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (
        CurrentUserPermission | IsAuthorOrAdminOrModerOrReadOnly,
    )
    pagination_class = LimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeWriteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer = RecipeSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        serializer = RecipeSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FavoriteViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer

    def get_queryset(self, obj):
        user = self.context.get('request').user
        return obj.favorite_recipe.filter(user=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        favorite_recipe = get_object_or_404(Recipe, id=recipe_id)
        Favorite.objects.create(
            user=request.user,
            favorite_recipe=favorite_recipe
        )
        serializer = FavoriteSerializer(favorite_recipe)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        favorite_recipe = get_object_or_404(Recipe, id=recipe_id)
        get_object_or_404(Favorite,
                          user=request.user,
                          favorite_recipe=favorite_recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated]
    queryset = ShoppingCart.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        ShoppingCart.objects.create(
            user=request.user,
            recipe=recipe)
        serializer = ShoppingCartSerializer(recipe)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        get_object_or_404(ShoppingCart,
                          user=request.user,
                          recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingListDownload(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.shopping_cart.all()

    def get(self, request):
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return self._create_shopping_list(self.get_queryset(), response)

    def _create_shopping_list(self, queryset, response):
        ingredients_and_amount = {}
        response.write('Список продуктов:\n')
        for item in queryset:
            ingredients_recipe = IngredientRecipe.objects.filter(
                recipe=item.recipe
            )
            for row in ingredients_recipe:
                ingredient = row.ingredient
                amount = row.amount
                if ingredient in ingredients_and_amount:
                    ingredients_and_amount[ingredient] += amount
                else:
                    ingredients_and_amount[ingredient] = amount
        for ingredient, amount in ingredients_and_amount.items():
            response.write(f'\n{ingredient.name}')
            response.write((f' ({ingredient.measurement_unit})'))
            response.write(f' - {amount}')
        return response
