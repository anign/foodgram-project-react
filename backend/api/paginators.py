from foodgram.settings import PAGE_LIMIT
from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    page_size = PAGE_LIMIT
