import os

import stripe
from _decimal import Decimal
from django.db import models

from borrowings.models import Borrowing


class Payment(models.Model):
    class StatusType(models.TextChoices):
        PENDING = "PENDING"
        PAID = "PAID"

    class TypeType(models.TextChoices):
        PAYMENT = "PAYMENT"
        FINE = "FINE"

    status = models.CharField(max_length=7, choices=StatusType.choices)
    type = models.CharField(max_length=7, choices=TypeType.choices)
    borrowing = models.OneToOneField(
        to=Borrowing, on_delete=models.CASCADE, related_name="payment"
    )
    stripe_session_url = models.URLField(null=True, blank=True)
    stripe_session_id = models.CharField(max_length=255, null=True, blank=True)

    @property
    def money_to_pay(self):
        if self.borrowing.actual_return_date:
            days_borrowed = (
                self.borrowing.actual_return_date - self.borrowing.borrow_date
            ).days
            return Decimal(days_borrowed) * self.borrowing.book.daily_fee
        return Decimal(0.01)

    def create_stripe_session(self, success_url, cancel_url):
        line_items = [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{self.type} for {self.borrowing.book.title}",
                    },
                    "unit_amount": int(self.money_to_pay * 100),
                },
                "quantity": 1,
            }
        ]
        stripe.api_key = os.getenv("STRIPE_API_KEY")
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
        )

        self.stripe_session_id = session["id"]
        self.stripe_session_url = session["url"]
        self.save()

        return session

    def __str__(self) -> str:
        return self.status
