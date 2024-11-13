import logging
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET
from .models import LinkMapped

logger = logging.getLogger(__name__)


@require_GET
def load_url(request, url_hash: str) -> HttpResponse:
    """Перенаправление."""
    try:
        original_url = get_object_or_404(
            LinkMapped,
            url_hash=url_hash
        ).original_url
        logger.info(f"Перенаправление с {url_hash} на {original_url}")
        return redirect(original_url)
    except Exception as e:
        logger.error(f"Ошибка перенаправления для {url_hash}: {str(e)}")
        return HttpResponse("Ошибка при перенаправлении", status=500)
