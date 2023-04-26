import datetime
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework import permissions
from rest_framework.viewsets import GenericViewSet

from notification.tasks import send_to_char_borrowing_book
from .models import Borrowing
from .serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
    BorrowingReturnSerializer,
)
from .permissions import IsTheUser


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        if self.action == "list":
            is_active_filter = self.request.query_params.get("is_active")
            if is_active_filter is True:
                return Borrowing.objects.filter(actual_return_date=None)
            elif self.request.user.is_superuser:
                user_id = self.request.query_params.get("user_id")
                if user_id:
                    return Borrowing.objects.filter(user=user_id)
                else:
                    return Borrowing.objects.all()
            else:
                return Borrowing.objects.filter(user=self.request.user)
        else:
            return super().get_queryset()

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer

        if self.action == "retrieve":
            return BorrowingDetailSerializer

        if self.action == "create":
            return BorrowingCreateSerializer

        if self.action == "return_book":
            return BorrowingReturnSerializer

        return BorrowingSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # send_to_char_borrowing_book.delay(
        #     request.data["book"],
        #     request.user.id,
        #     request.data["expected_return_date"]
        # )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(
        methods=["POST"],
        detail=True,
        url_path="return",
        permission_classes=[IsTheUser],
    )
    def return_book(self, request, pk=None):
        """The user that borrowed the book can return it"""
        borrowing = get_object_or_404(Borrowing, pk=pk)

        if borrowing.actual_return_date:
            return Response(
                {"error": "The book has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if borrowing.user_id != request.user.id:
            return Response(
                {"error": "You are not authorized to return this book."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        borrowing.actual_return_date = datetime.date.today()
        borrowing.save()
        book = borrowing.book
        book.inventory += 1
        book.save()

        return Response(
            {"success": "The book was successfully returned."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "is_active",
                type=OpenApiTypes.BOOL,
                description="Filter if books already returned or not (ex. ?is_active=True)",
            ),
            OpenApiParameter(
                "user_id",
                type=OpenApiTypes.INT,
                description="If user is admin he can filter by user id (ex. ?user_id=1)"
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(self, request, *args, **kwargs)
