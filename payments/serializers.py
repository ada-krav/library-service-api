from django.urls import reverse
from .models import Payment
from rest_framework import serializers, request


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing",
            "stripe_session_url",
            "stripe_session_id",
            "money_to_pay",
        )

    # def create(self, validated_data):
    #     # Создаем Stripe-сессию
    #     # Your code here
    #
    #     # Добавляем URL-адреса для SuccessView и CancelView
    #     success_url = request.build_absolute_uri(reverse("success"))
    #     cancel_url = request.build_absolute_uri(reverse("cancel"))
    #     # Your code here
    #
    #     return session_id