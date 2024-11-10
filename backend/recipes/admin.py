from django.contrib import admin

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag, TagRecipe


class TagRecipeInline(admin.TabularInline):
    model = TagRecipe
    extra = 1


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (TagRecipeInline, IngredientRecipeInline)
    list_display = ("name", "author", "favorite_count_display")
    search_fields = ("author__username", "name")
    list_filter = ("tags",)
    readonly_fields = ("favorite_count_display", "short_link")

    @admin.display(description="Добавили в Избранное")
    def favorite_count_display(self, obj):
        return obj.favorited_by.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)
