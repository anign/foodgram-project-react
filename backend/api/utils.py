from datetime import datetime

from django.shortcuts import HttpResponse, get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from .serializers import RecipeReadSerializer

from recipes.models import Recipe


def favorite_shopping_cart(self, request, model, **kwargs):
    recipe = get_object_or_404(Recipe, id=kwargs['pk'])

    if request.method == 'POST':
        serializer = RecipeReadSerializer(recipe, data=request.data,
                                      context={"request": request})
        serializer.is_valid(raise_exception=True)
        if not model.objects.filter(user=request.user,
                                    recipe=recipe).exists():
            model.objects.create(user=request.user, recipe=recipe)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response({'errors': 'Рецепт уже добавлен.'},
                        status=status.HTTP_400_BAD_REQUEST)

    get_object_or_404(model, user=request.user,
                      recipe=recipe).delete()
    return Response({'detail': 'Рецепт успешно удален.'},
                    status=status.HTTP_204_NO_CONTENT)


def ingredients_export(self, request, ingredients):
    user = request.user
    filename = f'{user.username}_shopping_list.txt'
    today = datetime.today()
    shopping_list = (
        f'Список покупок для: {user.get_full_name()}\n\n'
        f'Дата: {today:%Y-%m-%d}\n\n'
    )
    shopping_list += '\n'.join([
        f'- {ingredient["ingredient__name"]} '
        f'({ingredient["ingredient__measurement_unit"]})'
        f' - {ingredient["amount"]}'
        for ingredient in ingredients
    ])
    shopping_list += f'\n\nFoodgram ({today:%Y})'
    response = HttpResponse(shopping_list, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response
