from rest_framework.pagination import PageNumberPagination


class FoodgramPagination(PageNumberPagination):
    """Пагинация через ?limit={число}."""

    def get_page_size(self, request):
        limit = request.query_params.get("limit", self.page_size)
        try:
            return int(limit)
        except ValueError:
            return self.page_size
