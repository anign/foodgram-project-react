from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')


class RecipeIngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through
    min_num = 1


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'count_favorites')
    list_filter = ('author', 'name', 'tags')
    inlines = (RecipeIngredientInline,)

    def count_favorites(self, obj):
        return obj.favorite_recipe.count()


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingCart)
admin.site.register(Favorite)
