import uuid

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from recipes.constants import (COOKING_TIME, LENGTH_INGREDIENT,
                               LENGTH_MESURE_UNIT, LENGTH_TAG,
                               LENGTH_TO_DISPLAY, MIN_AMOUNT,
                               RECIPE_NAME_LENGTH, SHORT_LINK_LENGTH)
from recipes.validators import validate_slug

User = get_user_model()


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField("Название", max_length=RECIPE_NAME_LENGTH)
    image = models.ImageField(
        upload_to="recipes/images/", verbose_name="Картинка"
    )
    text = models.TextField("Описание")
    ingredients = models.ManyToManyField(
        "Ingredient",
        through="IngredientRecipe",
        verbose_name="Ингредиенты",
        related_name="recipes",
    )
    tags = models.ManyToManyField(
        "Tag", through="TagRecipe", verbose_name="Теги", related_name="recipes"
    )
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления (в минутах)",
        blank=False,
        validators=[MinValueValidator(COOKING_TIME)],
    )
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)
    short_link = models.CharField(
        "Короткая ссылка",
        max_length=SHORT_LINK_LENGTH,
        unique=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-pub_date"]

    def save(self, *args, **kwargs):
        """Генерирует уникальную короткую ссылку на рецепт."""
        if not self.short_link:
            self.short_link = str(uuid.uuid4())[:SHORT_LINK_LENGTH]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name[:LENGTH_TO_DISPLAY]


class Tag(models.Model):
    name = models.CharField("Название", max_length=LENGTH_TAG)
    slug = models.SlugField(
        "Cлаг", max_length=LENGTH_TAG, validators=[validate_slug], unique=True
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name[:LENGTH_TO_DISPLAY]


class Ingredient(models.Model):
    name = models.CharField("Название", max_length=LENGTH_INGREDIENT)
    measurement_unit = models.CharField(
        "Единица измерения", max_length=LENGTH_MESURE_UNIT
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name[:LENGTH_TO_DISPLAY]


class TagRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name="recipe_tags",
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    tag = models.ForeignKey(
        Tag,
        related_name="tag_recipes",
        on_delete=models.CASCADE,
        verbose_name="Теги",
    )

    class Meta:
        verbose_name = "Тег рецепта"
        verbose_name_plural = "Теги рецепта"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "tag"], name="unique_recipe_tag"
            )
        ]

    def __str__(self):
        return f"{self.recipe} {self.tag}"


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name="recipe_ingredients",
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name="ingredient_in_recipes",
        on_delete=models.CASCADE,
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        "Количество",
        validators=[MinValueValidator(MIN_AMOUNT)],
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            )
        ]

    def __str__(self):
        return f"{self.recipe} {self.ingredient}"


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        related_name="favorites",
        on_delete=models.CASCADE,
        verbose_name="Пользователи",
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="favorited_by",
        on_delete=models.CASCADE,
        verbose_name="Рецепты",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_fav_recipe"
            )
        ]

    def __str__(self):
        return f"{self.user} {self.recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        related_name="in_cart",
        on_delete=models.CASCADE,
        verbose_name="Пользователи",
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="cart_users",
        on_delete=models.CASCADE,
        verbose_name="Рецепты",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Список покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_recipe_in_cart"
            )
        ]

    def __str__(self):
        return f"{self.user} {self.recipe}"
