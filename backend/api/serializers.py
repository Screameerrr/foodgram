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
    """Сериализатор для модели пользователя."""

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
        if current_user.is_authenticated and current_user != obj:
            return Subscriber.objects.filter(user=current_user, author=obj).exists()
        return False


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара пользователя."""

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
    """Сериализатор для ингредиентов при создании нового рецепта."""

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
    """Сериализатор для краткого отображения рецепта."""

    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецепта."""

    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientGetSerializer(
        many=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return FavoriteRecipe.objects.filter(author=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(author=user, recipe=obj).exists()
        return False


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

    def validate(self, data):
        """Проверяет корректность введённых данных при создании рецепта."""
        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError({'tags': 'Добавьте хотя бы один тег.'})

        if len(set(tags)) != len(tags):
            raise serializers.ValidationError({'tags': 'Теги должны быть уникальными.'})

        ingredients = data.get('recipe_ingredients', [])
        if not ingredients:
            raise serializers.ValidationError({'ingredients': 'Добавьте хотя бы один ингредиент.'})

        ingredient_ids = [ingredient['ingredient'].id for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({'ingredients': 'Ингредиенты должны быть уникальными.'})

        return data

    def create(self, validated_data):
        """Создаёт новый рецепт."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        with transaction.atomic():
            recipe = Recipe.objects.create(**validated_data)  # Убрали author=author
            recipe.author = self.context['request'].user  # Устанавливаем автора
            recipe.save()
            recipe.tags.set(tags)
            self._add_ingredients(recipe, ingredients)
            return recipe

    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        image = validated_data.get('image', instance.image)
        if not image:
            raise serializers.ValidationError({'image': 'Изображение рецепта обязательно для заполнения.'})

        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('recipe_ingredients', None)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients is not None:
            instance.ingredients.clear()
            self._add_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def _add_ingredients(self, recipe, ingredients):
        """Вспомогательный метод для добавления ингредиентов к рецепту."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ])

    def to_representation(self, instance):
        """Возвращает представление рецепта после создания или обновления."""
        return RecipeSerializer(instance, context=self.context).data

    def validate_image(self, value):
        """Валидирует поле image."""
        if not value:
            raise serializers.ValidationError('Изображение рецепта обязательно для заполнения.')
        return value


class AuthorRecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для избранного и корзины."""

    class Meta:
        model = None
        fields = ('id', 'author', 'recipe')
        read_only_fields = ('id', 'author')

    def validate(self, data):
        """Проверяет, что рецепт ещё не добавлен в избранное или корзину."""
        recipe = data['recipe']
        user = self.context['request'].user
        if self.Meta.model.objects.filter(author=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт уже добавлен в {self.add_recipe}.'
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
        fields = ('id', 'author', 'recipe')


class ShoppingCartSerializer(AuthorRecipeSerializer):
    """Сериализатор для добавления рецепта в корзину покупок."""

    add_recipe = 'корзину покупок'

    class Meta(AuthorRecipeSerializer.Meta):
        model = ShoppingCart
        fields = ('id', 'author', 'recipe')


class UserRecipeSerializer(UserSerializer):
    """Сериализатор для отображения пользователя с его рецептами."""

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
        """Получает рецепты пользователя с возможностью ограничения по количеству."""
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except (ValueError, TypeError):
                pass

        return ShortRecipeSerializer(recipes, many=True, context=self.context).data


class ShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор для создания короткой ссылки."""

    short_link = serializers.SerializerMethodField()

    class Meta:
        model = LinkMapped
        fields = ('original_url', 'short_link')
        extra_kwargs = {'original_url': {'write_only': True}}

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

    class Meta:
        model = Subscriber
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscriber.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя.',
            )
        ]

    def validate(self, data):
        """Проверяет, что пользователь не подписывается сам на себя."""
        if data['user'] == data['author']:
            raise serializers.ValidationError('Нельзя подписаться на самого себя.')
        return data

    def to_representation(self, instance):
        """Возвращает информацию об авторе и его рецептах."""
        return UserRecipeSerializer(
            instance.author,
            context=self.context
        ).data
