from django.db import models


class Book(models.Model):
    class CoverType(models.TextChoices):
        HARD = "HD", "Hard"
        SOFT = "ST", "Soft"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=2, choices=CoverType.choices)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self) -> str:
        return self.title
