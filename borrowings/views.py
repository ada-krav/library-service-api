from django_filters import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics
from .models import Borrowing
from .serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer
)


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer

        if self.action == "retrieve":
            return BorrowingDetailSerializer

        if self.action == "create":
            return BorrowingCreateSerializer

        return BorrowingSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BorrowingList(generics.ListCreateAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def get_queryset(self):
        is_active_filter = self.request.query_params.get('is_active')
        if is_active_filter is True:
            return Borrowing.objects.filter(actual_return_date=None)

        if not self.request.user.is_authenticated:
            return Borrowing.objects.none()
        elif self.request.user.is_superuser:
            user_id = self.request.query_params.get('user_id')
            if user_id:
                return Borrowing.objects.filter(user=user_id)
            else:
                return Borrowing.objects.all()
        else:
            return Borrowing.objects.filter(user=self.request.user)
