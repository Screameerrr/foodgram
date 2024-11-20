from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(
    'users',
    views.UserViewSet,
    basename='users'
)
router.register(
    r'tags',
    views.TagViewSet,
    basename='tags'
)
router.register(
    r'recipes',
    views.RecipeViewSet,
    basename='recipes'
)
router.register(
    r'ingredients',
    views.IngredientViewSet,
    basename='ingredients'
)

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
