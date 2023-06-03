from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import SubscriptionsHandlingUserViewSet

from .views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                    FavouriteViewSet, ShoppingCartViewSet)

app_name = 'api'

router = DefaultRouter()

router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', SubscriptionsHandlingUserViewSet, basename='users')
router.register(
    r'recipes/(?P<recipe_id>\d+)/favorite',
    FavouriteViewSet,
    basename='favorite'
)
router.register(
    r'recipes/(?P<recipe_id>\d+)/shopping_cart',
    ShoppingCartViewSet,
    basename='shopping_cart'
)


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
