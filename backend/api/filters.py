from django.contrib.auth import get_user_model
from django_filters.rest_framework import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    AllValuesMultipleFilter,
)

from recipes.models import (
    Ingredient,
    Recipe,
)

User = get_user_model()


class IngredientFilter(FilterSet):
    """Фильтр для ингредиентов."""

    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """Фильтр для рецептов."""

    tags = AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def filter_by_relation(self, queryset, relation_name, value):
        """
        Универсальный метод фильтрации по отношению.
        """
        user = self.request.user
        if not user.is_authenticated:
            return queryset
        if value:
            return queryset.filter(**{f"{relation_name}__author": user})
        return queryset.exclude(**{f"{relation_name}__author": user})

    def filter_is_favorited(self, queryset, name, value):
        return self.filter_by_relation(
            queryset,
            "favorites",
            value
        )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self.filter_by_relation(
            queryset,
            "shopping_cart",
            value
        )
