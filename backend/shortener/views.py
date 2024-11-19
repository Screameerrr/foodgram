import logging
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from shortener.models import LinkMapped

logger = logging.getLogger(__name__)


@require_GET
def load_url(request, url_hash: str) -> JsonResponse:
    """Перенаправление."""
    try:
        link = LinkMapped.objects.filter(url_hash=url_hash).first()
        if not link:
            return JsonResponse(
                {"error": "Ссылка не найдена"},
                status=200
            )
        original_url = link.original_url
        logger.info(f"Перенаправление с {url_hash} на {original_url}")
        return JsonResponse(
            {"redirect": original_url},
            status=200
        )
    except Exception as e:
        logger.error(f"Ошибка перенаправления для {url_hash}: {str(e)}")
        return JsonResponse(
            {"error": "Ошибка при перенаправлении"},
            status=500
        )
