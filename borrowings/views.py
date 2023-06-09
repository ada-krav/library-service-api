import datetime

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter

from rest_framework import status, mixins, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from config import settings
from notification.tasks import send_to_chat_borrowing_book

from payments.utils import create_payment_and_stripe_session
from .models import Borrowing
from .serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
    BorrowingReturnSerializer,
)
from .permissions import IsTheUser


SUCCESS_URL = (
    f"{settings.DOMAIN_URL}/payments/success?session_id={{CHECKOUT_SESSION_ID}}"
)
CANCEL_URL = f"{settings.DOMAIN_URL}/payments/cancel?session_id={{CHECKOUT_SESSION_ID}}"


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        queryset = self.queryset
        is_active_filter = self.request.query_params.get("is_active")

        if is_active_filter in ("True", "true"):
            queryset = queryset.filter(actual_return_date__isnull=True)

        if is_active_filter in ("False", "false"):
            queryset = queryset.filter(actual_return_date__isnull=False)

        if self.request.user.is_staff:
            user_id = self.request.query_params.get("user_id")

            if user_id:
                queryset = queryset.filter(user=user_id)
        else:
            queryset = queryset.filter(user=self.request.user)

        return queryset

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
        self.perform_create(serializer)
        send_to_chat_borrowing_book.delay(
                request.data["book"],
                request.user.id,
                request.data["expected_return_date"]
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
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
        with transaction.atomic():
            borrowing.actual_return_date = datetime.date.today()
            borrowing.save()
            book = borrowing.book
            book.inventory += 1
            book.save()
            if borrowing.actual_return_date > borrowing.expected_return_date:
                payment = create_payment_and_stripe_session(
                    borrowing,
                    success_url=SUCCESS_URL,
                    cancel_url=CANCEL_URL,
                    payment_type="FINE",
                )
                return Response(
                    {
                        "success": "The book was successfully returned.",
                        "message": "Your borrowing was overdue. You`ll have to pay fine.",
                        "link": f"Pay here: {payment.stripe_session_url}"
                    },
                    status=status.HTTP_200_OK,
                )
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
                description="If user is admin he can filter by user id (ex. ?user_id=1)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(self, request, *args, **kwargs)
