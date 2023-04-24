from rest_framework import viewsets, permissions

from .models import Book
from .permissions import IsAdminUser
from .serializers import BookSerializer


class BookViewSets(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminUser | permissions.IsAuthenticatedOrReadOnly]
