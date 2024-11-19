from django.http import FileResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from djoser import views as djoser_views

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import FoodgramPagination
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    ShortLinkSerializer,
    SubscribeSerializer,
    TagSerializer,
    UserRecipeSerializer,
)
from .utils import pdf_shopping_list, ingredients_list
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag
)
from shortener.models import LinkMapped
from users.models import Subscriber

User = get_user_model()


class UserViewSet(djoser_views.UserViewSet):
    """Вьюсет для управления пользователями."""

    pagination_class = FoodgramPagination

    @action(
        methods=['put'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        """Обновление аватара пользователя."""
        serializer = AvatarSerializer(
            self.get_instance(),
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара пользователя."""
        data = {'avatar': None}
        serializer = AvatarSerializer(
            self.get_instance(),
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """Получение списка подписок пользователя."""
        queryset = User.objects.filter(
            subscribers__user=request.user
        ).prefetch_related('recipes').order_by(
            'id')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserRecipeSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserRecipeSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
    )
    def subscribe(self, request, id):
        """Подписка на автора по его ID."""
        author = get_object_or_404(User, id=id)
        serializer = SubscribeSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        """Отписка от автора по его ID."""
        author = get_object_or_404(User, id=id)
        subscription = Subscriber.objects.filter(
            user=request.user,
            author=author
        )
        if not subscription.exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        """Получение информации о текущем пользователе."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)



class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    permission_classes = [permissions.AllowAny]


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления рецептами."""

    queryset = Recipe.objects.all()
    pagination_class = FoodgramPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]  # Убедитесь, что оба класса указаны

    def get_serializer_class(self):
        """Получение сериализатора в зависимости от действия."""
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        """Сохранение автора при создании рецепта."""
        serializer.save(author=self.request.user)


    def handle_action(
            self,
            request,
            pk,
            model_class,
            serializer_class,
            error_message
    ):
        """Общий метод для добавления и удаления рецепта."""
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            serializer = serializer_class(
                data={'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        item = model_class.objects.filter(author=request.user, recipe=recipe)
        if not item.exists():
            return Response({'errors': error_message},
                            status=status.HTTP_400_BAD_REQUEST
                            )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        """Добавление или удаление рецепта из корзины покупок."""
        return self.handle_action(
            request,
            pk,
            model_class=ShoppingCart,
            serializer_class=ShoppingCartSerializer,
            error_message='Рецепт не найден в корзине.'
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        """Добавление или удаление рецепта из избранного."""
        return self.handle_action(
            request,
            pk,
            model_class=FavoriteRecipe,
            serializer_class=FavoriteSerializer,
            error_message='Рецепт не найден в избранном.'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в формате PDF."""
        recipes = Recipe.objects.filter(
            shopping_cart__author=request.user
        )
        shopping_list = ingredients_list(recipes)
        buffer = pdf_shopping_list(shopping_list, request.user)
        response = FileResponse(
            buffer,
            content_type='application/pdf'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.pdf"'
        )
        return response

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[AllowAny],
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = self.get_object()
        original_url = request.build_absolute_uri(
            reverse('api:recipes-detail', args=[recipe.id])
        )
        link, created = LinkMapped.objects.get_or_create(
            original_url=original_url
        )
        serializer = ShortLinkSerializer(link, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
