from django.contrib.auth import get_user_model
from django_filters.rest_framework import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    ModelMultipleChoiceFilter,
)

from recipes.models import (
    Ingredient,
    Recipe,
    Tag
)

User = get_user_model()


class IngredientFilter(FilterSet):
    """Ингредиенты"""

    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """Рецепты"""

    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorited = BooleanFilter(
        method='is_favorite_filter',
        field_name='favorites__author',
    )
    is_in_shopping_cart = BooleanFilter(
        method='is_in_shopping_cart_filter',
        field_name='shopping_cart__author',
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def is_favorite_filter(self, queryset, name, value):
        return self.filter_from_kwargs(
            queryset,
            value,
            name,
        )

    def is_in_shopping_cart_filter(self, queryset, name, value):
        return self.filter_from_kwargs(
            queryset,
            value,
            name,
        )

    def filter_from_kwargs(self, queryset, value, name):
        if value and self.request.user.id:
            return queryset.filter(**{name: self.request.user})
        return queryset
