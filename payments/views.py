from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from .models import Payment
from .permissions import IsAdminOrSelf
from .serializers import PaymentSerializer


class PaymentList(generics.ListCreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(borrowing__user=user)


class PaymentDetail(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminOrSelf)

    def get_object(self):
        obj = get_object_or_404(Payment, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj
