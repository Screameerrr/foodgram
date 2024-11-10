from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from recipes.models import Favorite, ShoppingCart
from users.models import Subscription, User


class FavoriteInline(admin.TabularInline):
    model = Favorite
    extra = 1
    fk_name = "user"


class ShoppingCartInline(admin.TabularInline):
    model = ShoppingCart
    extra = 1
    fk_name = "user"


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 1
    fk_name = "user"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "first_name", "last_name", "email")
    search_fields = ("username", "email")
    inlines = (SubscriptionInline, FavoriteInline, ShoppingCartInline)
