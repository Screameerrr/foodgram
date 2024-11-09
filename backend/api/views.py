from django.db.models import Exists, OuterRef
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from djoser import views as djoser_views

from api.filters import (
    IngredientFilter,
    RecipeFilter
)
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
)
from .utils import (
    pdf_shopping_list,
    ingredients_list,
)
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscriber

User = get_user_model()


class UserViewSet(djoser_views.UserViewSet):
    """Пользователь"""

    pagination_class = FoodgramPagination

    def get_queryset(self):
        user = self.request.user
        if self.action in ('list', 'retrieve'):
            return (
                User.objects.prefetch_related(
                    Subscriber.get_prefetch_subscribers(
                        'subscribers',
                        user
                    ),
                )
                .order_by('id')
                .all()
            )

        if self.action in ('subscriptions',):
            return (
                Subscriber.objects.subscriber
                .prefetch_related(
                    Subscriber.get_prefetch_subscribers(
                        'author__subscribers',
                        user
                    ),
                    'author__recipes',
                )
                .order_by('id')
                .all()
            )

        if self.action in ('subscribe',):
            return User.objects.prefetch_related(
                Subscriber.get_prefetch_subscribers(
                    'subscribers',
                    user
                ),
            ).all()

        return User.objects.all()

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_name='me',
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        methods=['put'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        url_name='me-avatar',
    )
    def avatar(self, request):
        """Аватар"""
        serializer = self._change_avatar(request.data)
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        data = request.data
        if 'avatar' not in data:
            data = {'avatar': None}
        self._change_avatar(data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        """Список подписок"""
        page = self.paginate_queryset(self.get_queryset())
        serializer = SubscribeSerializer(
            page, many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, id):
        """Подписка"""
        serializer = SubscribeSerializer(
            data={'author': self.get_object()},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        subscriber_deleted, _ = request.user.subscriber.filter(
            author=self.get_object()
        ).delete()

        if subscriber_deleted == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _change_avatar(self, data):
        instance = self.get_instance()
        serializer = AvatarSerializer(
            instance,
            data=data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Тег"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Ингредиент"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепт"""

    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = FoodgramPagination
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        fun_action = {
            'list': RecipeSerializer,
            'retrieve': RecipeSerializer,
            'get_link': ShortLinkSerializer,
            'favorite': FavoriteSerializer,
            'shopping_cart': ShoppingCartSerializer,
        }
        return fun_action.get(self.action, RecipeCreateSerializer)

    def get_queryset(self):
        user = self.request.user
        robj = Recipe.objects
        if self.action in ['list', 'retrieve']:
            robj = (
                robj.select_related('author')
                .prefetch_related(
                    'recipe_ingredients__ingredient',
                    'recipe_ingredients',
                    'tags',
                    Subscriber.get_prefetch_subscribers(
                        'author__subscribers',
                        user
                    ),
                )
                .annotate(
                    is_favorited=Exists(
                        user.favorite_recipes.filter(
                            recipe=OuterRef('pk')
                        )
                    ),
                    is_in_shopping_cart=Exists(
                        user.shopping_cart_recipes.filter(
                            recipe=OuterRef('pk')
                        )
                    ),
                )
                .all()
            )

        return robj.order_by('-created_at').all()

    @action(
        methods=['post'],
        detail=True,
        url_name='shopping-cart',
    )
    def shopping_cart(self, request, pk=None):
        request = get_object_or_404(Recipe, pk=pk)
        return self._post_author_recipe(request, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self._delete_author_recipe(request, pk, ShoppingCart)

    @action(
        methods=['post'],
        detail=True,
    )
    def favorite(self, request, pk=None):
        request = get_object_or_404(Recipe, pk=pk)
        return self._post_author_recipe(request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self._delete_author_recipe(request, pk, FavoriteRecipe)

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link',
        url_name='get-link',
    )
    def get_link(self, request, pk=None):
        """ссылка для рецепта"""
        self.get_object()
        original_url = request.META.get('HTTP_REFERER')
        if original_url is None:
            url = reverse('api:recipe-detail', kwargs={'pk': pk})
            original_url = request.build_absolute_uri(url)
        serializer = self.get_serializer(
            data={'original_url': original_url},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def _post_author_recipe(self, request, pk):
        serializer = self.get_serializer(data=dict(recipe=pk))
        serializer.is_valid(raise_exception=True)
        serializer.save(author=self.request.user)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def _delete_author_recipe(self, request, pk, model):
        recipe = get_object_or_404(Recipe, pk=pk)
        obj_count, _ = model.objects.filter(
            author=self.request.user,
            recipe=recipe,
        ).delete()

        if obj_count == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request, file_ext='pdf'):
        user = request.user
        author_shopping_list = Recipe.objects.filter(
            shopping_cart__author=user)
        shopping_list = ingredients_list(author_shopping_list)

        if file_ext != 'pdf':
            return Response(
                {'detail': 'Недопустимый формат файла.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        content_type = 'application/pdf'
        buffer = pdf_shopping_list(
            shopping_list,
            user
        )
        response = FileResponse(
            buffer,
            content_type=content_type
        )
        filename = f'{user.username}_shopping_cart.{file_ext}'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
