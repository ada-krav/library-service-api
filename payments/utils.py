import stripe
from _decimal import Decimal
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

from .models import Payment

stripe.api_key = settings.STRIPE_API_KEY

FINE_MULTIPLIER = 2


def create_payment_and_stripe_session(borrowing, success_url, cancel_url, payment_type):
    if payment_type == "PAYMENT":
        days_borrowed = borrowing.expected_return_date - borrowing.borrow_date
        money_to_pay = Decimal(days_borrowed.days) * borrowing.book.daily_fee
        payment_type = Payment.TypeType.PAYMENT

    elif payment_type == "FINE":
        days_overdue = (
            borrowing.actual_return_date - borrowing.expected_return_date
        ).days
        money_to_pay = (
            Decimal(days_overdue) * borrowing.book.daily_fee * FINE_MULTIPLIER
        )
        payment_type = Payment.TypeType.FINE
    else:
        return Response(
            {"error": "Payment type has to be either PAYMENT or FINE"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    line_items = [
        {
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"{payment_type} for {borrowing.book.title}",
                },
                "unit_amount": int(money_to_pay * 100),
            },
            "quantity": 1,
        }
    ]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )

    payment = Payment.objects.create(
        borrowing=borrowing,
        stripe_session_url=session["url"],
        stripe_session_id=session["id"],
        status=Payment.StatusType.PENDING,
        type=payment_type,
    )

    return payment
