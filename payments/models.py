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
    borrowing = models.OneToOneField(to=Borrowing, on_delete=models.CASCADE, related_name="payment")
    session_url = models.URLField()
    session_id = models.CharField(max_length=255)

    @property
    def money_to_pay(self):
        if self.borrowing.actual_return_date:
            days_borrowed = (self.borrowing.actual_return_date - self.borrowing.borrow_date).days
            return Decimal(days_borrowed) * self.borrowing.book.daily_fee
        return Decimal(0)

    def __str__(self) -> str:
        return self.status
