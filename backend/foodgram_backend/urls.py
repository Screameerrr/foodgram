from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from api.views import ReturnShortLinkRecipeAPI

urlpatterns = [
    path("api/", include("api.urls")),
    path("admin/", admin.site.urls),
    path(
        "s/<str:short_link>/",
        ReturnShortLinkRecipeAPI.as_view(),
        name="recipe-short-link",
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
