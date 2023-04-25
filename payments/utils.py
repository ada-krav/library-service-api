import stripe
from _decimal import Decimal
from django.conf import settings
from .models import Payment

stripe.api_key = settings.STRIPE_API_KEY


def create_payment_and_stripe_session(borrowing, success_url, cancel_url, payment_type):
    days_borrowed = (borrowing.expected_return_date - borrowing.borrow_date).days
    total_price = Decimal(days_borrowed) * borrowing.book.daily_fee

    line_items = [
        {
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"{payment_type} for {borrowing.book.title}",
                },
                "unit_amount": int(total_price * 100),
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
