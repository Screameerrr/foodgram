from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    r'users',
    views.UserViewSet,
    'users'
)
router.register(
    r'tags',
    views.TagViewSet,
    'tag'
)
router.register(
    r'recipes',
    views.RecipeViewSet,
    'recipe'
)
router.register(
    r'ingredients',
    views.IngredientViewSet,
    'ingredient'
)
app_name = 'api'

urlpatterns = [

    path('', include(router.urls)),
    path(r'auth/', include('djoser.urls.authtoken')),
]
