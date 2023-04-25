from django.urls import path
from .views import PaymentList, PaymentDetail, create_stripe_session

urlpatterns = [
    path("payments/", PaymentList.as_view(), name="payment_list"),
    path("payments/<int:pk>/", PaymentDetail.as_view(), name="payment_detail"),
    path(
        "payments/<int:pk>/create-stripe-session/",
        create_stripe_session,
        name="create_stripe_session",
    ),
]

app_name = "payments"
