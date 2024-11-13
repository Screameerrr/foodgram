from django.db import transaction
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.validators import UniqueTogetherValidator

from api.constants import (
    COOKING_TIME_MAX,
    COOKING_TIME_MIN,
    AMOUNT_MAX,
    AMOUNT_MIN
)
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from shortener.models import LinkMapped
from users.models import Subscriber

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели пользователя.

    Отображает информацию о пользователе и определяет поле `is_subscribed`,
    которое показывает, подписан ли текущий пользователь на данного автора.
    """

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного автора."""
        current_user = self.context['request'].user
        if hasattr(obj, 'subs'):
            return bool(obj.subs and obj.subs[0].is_subscribed)
        return (
            current_user.is_authenticated
            and current_user != obj
            and obj.subscribers.filter(user=current_user).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара пользователя.

    Позволяет загружать и обновлять аватар пользователя.
    """

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели тега."""

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug'
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиента."""

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов при создании нового рецепта.

    Используется для добавления ингредиентов в рецепт.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(
        max_value=AMOUNT_MAX,
        min_value=AMOUNT_MIN,
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount'
        )


class IngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов в рецепте."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения рецепта.

    Используется в списках, избранном и подписках.
    """

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецепта.

    Отображает подробную информацию о рецепте, включая автора, ингредиенты,
    теги и статус избранного или добавленного в корзину.
    """

    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    tags = TagSerializer(many=True)
    ingredients = IngredientGetSerializer(
        many=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.BooleanField(
        default=False,
        read_only=True
    )
    is_in_shopping_cart = serializers.BooleanField(
        default=False,
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        max_value=COOKING_TIME_MAX,
        min_value=COOKING_TIME_MIN,
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_image(self, image_data):
        """Валидирует наличие изображения."""
        if image_data is None:
            raise serializers.ValidationError(
                'Добавьте изображение.'
            )
        return image_data

    def validate(self, data):
        """Проверяет корректность введённых данных при создании рецепта."""
        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError('Добавьте тег.')

        if len(set(tags)) != len(tags):
            raise serializers.ValidationError('Теги должны быть уникальными.')

        ingredients = data.get('recipe_ingredients', [])
        if not ingredients:
            raise serializers.ValidationError('Добавьте ингредиент.')

        id_ingredients = {
            ingredient['ingredient'] for ingredient in ingredients
        }
        if len(ingredients) != len(id_ingredients):
            raise (serializers.
                   ValidationError('Ингредиенты должны быть уникальными.')
                   )
        return data

    def create(self, validated_data):
        """Создаёт новый рецепт."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        with transaction.atomic():
            recipe = Recipe.objects.create(**validated_data)
            self.add_tags_and_ingredients_to_recipe(
                recipe,
                tags,
                ingredients
            )
            return recipe

    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        with transaction.atomic():
            instance.ingredients.clear()
            instance.tags.clear()
            self.add_tags_and_ingredients_to_recipe(
                instance,
                tags,
                ingredients
            )
            super().update(instance, validated_data)
            return instance

    @staticmethod
    def add_tags_and_ingredients_to_recipe(recipe, tags, ingredients):
        """Добавляет теги и ингредиенты к рецепту."""
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        )

    def to_representation(self, instance):
        """Возвращает представление рецепта после создания или обновления."""
        return RecipeSerializer(instance, context=self.context).data


class AuthorRecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для избранного и корзины.

    Используется для добавления и удаления рецептов из избранного и корзины.
    """

    add_recipe: str = None

    class Meta:
        model = None
        fields = (
            'author',
            'recipe'
        )
        read_only_fields = ('author',)

    def validate(self, data):
        """Проверяет, что рецепт ещё не добавлен в избранное или корзину."""
        recipe = data['recipe']
        user = self.context['request'].user
        if self.Meta.model.objects.filter(
            author=user,
            recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                f'Рецепт уже добавлен в {self.add_recipe}'
            )
        return data

    def to_representation(self, instance):
        """Возвращает краткое представление рецепта."""
        return ShortRecipeSerializer(
            instance.recipe,
            context=self.context
        ).data


class FavoriteSerializer(AuthorRecipeSerializer):
    """Сериализатор для добавления рецепта в избранное."""

    add_recipe = 'избранное'

    class Meta(AuthorRecipeSerializer.Meta):
        model = FavoriteRecipe


class ShoppingCartSerializer(AuthorRecipeSerializer):
    """Сериализатор для добавления рецепта в корзину покупок."""

    add_recipe = 'корзину покупок'

    class Meta(AuthorRecipeSerializer.Meta):
        model = ShoppingCart


class UserRecipeSerializer(UserSerializer):
    """Сериализатор для отображения пользователя с его рецептами.

    Используется в подписках для отображения автора и его рецептов.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        read_only=True, source='recipes.count'
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_recipes(self, obj):
        """Получает рецепты пользователя
        с возможностью ограничения по количеству."""
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except (ValueError, TypeError):
                pass

        return ShortRecipeSerializer(recipes, many=True).data


class ShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор для создания короткой ссылки."""

    class Meta:
        model = LinkMapped
        fields = ('original_url',)
        write_only_fields = ('original_url',)

    def get_short_link(self, obj):
        """Генерирует короткую ссылку на основе хэша."""
        request = self.context.get('request')
        return request.build_absolute_uri(
            reverse(
                'shortener:load_url',
                args=[obj.url_hash]
            )
        )

    def create(self, validated_data):
        """Создаёт или получает существующую короткую ссылку."""
        instance, _ = LinkMapped.objects.get_or_create(**validated_data)
        return instance

    def to_representation(self, instance):
        """Возвращает короткую ссылку в ответе."""
        return {'short-link': self.get_short_link(instance)}


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки на авторов."""

    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='email',
        default=serializers.CurrentUserDefault(),
    )
    author = serializers.SlugRelatedField(
        slug_field='email',
        queryset=User.objects.all(),
    )

    class Meta:
        model = Subscriber
        fields = (
            'author',
            'user'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=(
                    'author',
                    'user'
                ),
                message='Вы уже подписаны',
            )
        ]

    def validate_author(self, author):
        """Проверяет, что пользователь не подписывается сам на себя."""
        if self.context['request'].user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        return author

    def to_representation(self, instance):
        """Возвращает информацию об авторе и его рецептах."""
        return UserRecipeSerializer(
            instance.author,
            context=self.context
        ).data
