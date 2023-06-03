from rest_framework.pagination import PageNumberPagination

from foodgram.settings import PAGE_LIMIT


class CustomPagination(PageNumberPagination):
    page_size = PAGE_LIMIT
