from django.urls import path
from .views import PaymentList, PaymentDetail

urlpatterns = [
    path('payments/', PaymentList.as_view(), name='payment_list'),
    path('payments/<int:pk>/', PaymentDetail.as_view(), name='payment_detail'),
]

app_name = "payments"
