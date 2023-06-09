import datetime

from rest_framework import serializers

from books.serializers import BookSerializer
from config import settings
from payments.serializers import PaymentSerializer
from payments.utils import create_payment_and_stripe_session
from users.serializers import UserSerializer
from borrowings.models import Borrowing


SUCCESS_URL = (
    f"{settings.DOMAIN_URL}/payments/success?session_id={{CHECKOUT_SESSION_ID}}"
)
CANCEL_URL = f"{settings.DOMAIN_URL}/payments/cancel?session_id={{CHECKOUT_SESSION_ID}}"


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        )


class BorrowingListSerializer(BorrowingSerializer):
    book = serializers.SlugRelatedField(read_only=True, slug_field="title")

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        )


class BorrowingDetailSerializer(BorrowingSerializer):
    book = BookSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    payments = PaymentSerializer(read_only=True, many=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "payments",
        )


class BorrowingCreateSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Borrowing
        fields = ("id", "book", "borrow_date", "expected_return_date", "payments")

    def validate(self, data):
        book = data["book"]
        if book.inventory <= 0:
            raise serializers.ValidationError("The book is not available.")

        borrow_date = datetime.date.today()
        expected_return_date = data["expected_return_date"]

        if expected_return_date < borrow_date:
            raise serializers.ValidationError(
                "The expected return date cannot be " "earlier than the borrow date."
            )

        return data

    def create(self, validated_data):
        book = validated_data["book"]
        book.inventory -= 1
        book.save()

        borrowing = Borrowing.objects.create(**validated_data)
        create_payment_and_stripe_session(
            borrowing,
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL,
            payment_type="PAYMENT",
        )

        return borrowing


class BorrowingReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "book",
        )
        read_only_fields = ("book", "expected_return_date")
