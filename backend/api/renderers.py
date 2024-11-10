from rest_framework.renderers import BaseRenderer


class PlainTextRenderer(BaseRenderer):
    """Конвертирует данные в plain text format."""

    media_type = "text/plain"
    format = "txt"
    charset = "utf-8"

    def render(self, data, media_type=None, renderer_context=None):
        if isinstance(data, dict):
            data = str(data)
        elif isinstance(data, list):
            data = "\n".join(data)
        return data.encode(self.charset)
