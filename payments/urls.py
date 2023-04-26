from django.urls import path
from .views import PaymentList, PaymentDetail, create_stripe_session, payment_success, payment_cancel

urlpatterns = [
    path("payments/", PaymentList.as_view(), name="payment_list"),
    path("payments/<int:pk>/", PaymentDetail.as_view(), name="payment_detail"),
    path(
        "payments/<int:pk>/create-stripe-session/",
        create_stripe_session,
        name="create_stripe_session",
    ),
    path("payment/success/", payment_success, name="payment_success"),
    path("payment/cancel/", payment_cancel, name="payment_cancel"),
    # path('payment/success/', SuccessView.as_view(), name='success'),
    # path('payment/cancel/', CancelView.as_view(), name='cancel'),
]

app_name = "payments"
