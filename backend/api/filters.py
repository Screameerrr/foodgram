from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Фильтр рецептов."""

    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )
    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(cart_users__user=self.request.user)
        return queryset


class IngredientFilter(filters.FilterSet):
    """Фильтр ингредиентов."""

    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Ingredient
        fields = ["name"]
