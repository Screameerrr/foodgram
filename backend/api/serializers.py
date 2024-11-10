import base64

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import Count, Exists
from djoser.serializers import TokenCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


def add_tags_and_ingredients(recipe, ingredients_data, tags_data):
    """Работает с тегами и ингредиентами при create/update рецепта."""
    recipe.tags.set(tags_data)

    for ingredient in ingredients_data:
        current_ingredient = ingredient["id"]

        IngredientRecipe.objects.update_or_create(
            recipe=recipe,
            ingredient=current_ingredient,
            amount=ingredient["amount"],
        )


class Base64ImageField(serializers.ImageField):
    """Декодирует изображение из base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class TokenLoginSerializer(TokenCreateSerializer):
    """Сериализатор для входа и получения токена."""

    username = None

    class Meta:
        model = User
        fields = ("email", "password")


class NewUserSerializer(UserSerializer):
    """Сериализатор информации о пользователе."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, subscribed_to=obj
            ).exists()
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.avatar:
            avatar_url = instance.avatar.url
            representation["avatar"] = f"{settings.BASE_URL}{avatar_url}"
        return representation


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя."""

    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "password")

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для игредиентов рецептов модели IngredientRecipe."""

    id = serializers.IntegerField(source="ingredient.id", read_only=True)
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )

    class Meta:
        model = IngredientRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения модели рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = NewUserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(
        many=True, source="recipe_ingredients"
    )
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            image_url = instance.image.url
            representation["image"] = f"{settings.BASE_URL}{image_url}"
        return representation


class IngredientRecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи игредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ("id", "amount")


class RecipeIWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи модели рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
        allow_empty=False,
        allow_null=False,
    )
    image = Base64ImageField()
    ingredients = IngredientRecipeWriteSerializer(many=True)
    is_favorited = serializers.BooleanField(default=False, read_only=True)
    is_in_shopping_cart = serializers.BooleanField(
        default=False, read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def validate(self, attrs):
        """Проверка обязательных полей."""
        required_fields = (
            "ingredients",
            "tags",
            "name",
            "text",
            "cooking_time",
        )
        if self.instance is None:
            required_fields += ("image",)
        missing_fields = []

        for field in required_fields:
            if field not in attrs or (
                isinstance(attrs[field], list) and not attrs[field]
            ):
                missing_fields.append(field)

        if missing_fields:
            raise serializers.ValidationError(
                {
                    "detail": [
                        f"Это поле {field} обязательное."
                        for field in missing_fields
                    ]
                }
            )

        cooking_time = attrs.get("cooking_time")
        if cooking_time is not None and cooking_time < 1:
            raise serializers.ValidationError(
                {"detail": "Время готовки должно быть минимум 1."}
            )

        ingredients_data = attrs.get("ingredients")
        if ingredients_data:
            seen_ingredients = set()
            for ingredient in ingredients_data:
                amount = ingredient.get("amount")
                cur_ingredient = ingredient.get("id")

                if amount is not None and amount < 1:
                    raise serializers.ValidationError(
                        {"detail": "amount должен быть не менее 1."}
                    )
                if cur_ingredient in seen_ingredients:
                    raise serializers.ValidationError(
                        {"detail": "Ингредиенты не должны повторяться."}
                    )
                seen_ingredients.add(cur_ingredient)

        tags_data = attrs.get("tags")
        if tags_data:
            tags_set = set(tags_data)
            if len(tags_data) != len(tags_set):
                raise serializers.ValidationError(
                    {"detail": "Теги не должны повторяться."}
                )

        return attrs

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")
        author = self.context["request"].user
        recipe = Recipe.objects.create(author=author, **validated_data)

        add_tags_and_ingredients(recipe, ingredients_data, tags_data)

        return recipe

    def update(self, instance, validated_data):
        if "image" in validated_data:
            instance.image = validated_data.pop("image")

        ingredients_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")
        add_tags_and_ingredients(instance, ingredients_data, tags_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Метод для возвращения данных, как при GET запросе."""
        serializer = RecipeReadSerializer(instance)
        return serializer.data


class RecipeRepresentation(serializers.ModelSerializer):
    """Сериализатор краткой информации о рецепте."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            image_url = instance.image.url
            representation["image"] = f"{settings.BASE_URL}{image_url}"
        return representation


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины с рецептами."""

    class Meta:
        model = ShoppingCart
        fields = ("recipe",)

    def create(self, validated_data):
        user = self.context["request"].user
        recipe = validated_data["recipe"]
        cart_item, created = ShoppingCart.objects.get_or_create(
            user=user, recipe=recipe
        )
        if not created:
            raise serializers.ValidationError(
                "Рецепт уже есть в списке покупок."
            )
        return cart_item

    def to_representation(self, instance):
        recipe = instance.recipe
        serializer = RecipeRepresentation(recipe)
        return serializer.data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов в Избранное."""

    class Meta:
        model = Favorite
        fields = ("recipe",)

    def create(self, validated_data):
        user = self.context["request"].user
        recipe = validated_data["recipe"]
        fav_item, created = Favorite.objects.get_or_create(
            user=user, recipe=recipe
        )
        if not created:
            raise serializers.ValidationError("Рецепт уже есть в Избранном.")
        return fav_item

    def to_representation(self, instance):
        recipe = instance.recipe
        serializer = RecipeRepresentation(recipe)
        return serializer.data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок."""

    is_subscribed = serializers.BooleanField()
    recipes = RecipeRepresentation(many=True)
    recipes_count = serializers.IntegerField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.avatar:
            avatar_url = instance.avatar.url
            representation["avatar"] = f"{settings.BASE_URL}{avatar_url}"
        return representation


class SubscribeActionSerializer(serializers.ModelSerializer):
    """Сериализатор пользователей для Подписок."""

    class Meta:
        model = Subscription
        fields = ("subscribed_to",)

    def create(self, validated_data):
        current_user = self.context["request"].user
        subscribed_to = validated_data["subscribed_to"]
        pair, created = Subscription.objects.get_or_create(
            user=current_user, subscribed_to=subscribed_to
        )
        if not created:
            raise serializers.ValidationError("""Подписка существует.""")
        return pair

    def to_representation(self, instance):
        subscribed_to = instance.subscribed_to
        context = {"current_user": instance.user}
        user_with_count = User.objects.annotate(
            recipes_count=Count("recipes"),
            is_subscribed=Exists(
                Subscription.objects.filter(
                    user=context["current_user"], subscribed_to=subscribed_to
                )
            ),
        ).get(id=subscribed_to.id)
        serializer = SubscriptionSerializer(user_with_count, context=context)
        return serializer.data


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор работы с аватаром."""

    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = ("avatar",)

    def validate(self, attrs):
        avatar = attrs.get("avatar", None)
        if avatar is None or (
            isinstance(avatar, str) and avatar.strip() == ""
        ):
            raise serializers.ValidationError(
                {"avatar": "Передаваемое поле не может быть пустым."}
            )
        return attrs

    def update(self, instance, validated_data):
        if "avatar" in validated_data and instance.avatar:
            instance.avatar.delete(save=False)
        return super().update(instance, validated_data)
