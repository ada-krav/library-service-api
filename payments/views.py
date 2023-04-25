from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

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


@api_view(["POST"])
def create_stripe_session(request, pk):
    try:
        payment = Payment.objects.get(pk=pk)
    except Payment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    success_url = "https://www.google.com/"
    cancel_url = "https://www.bing.com/"

    if not success_url or not cancel_url:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    session = payment.create_stripe_session(success_url, cancel_url)

    return Response(
        {
            "session_id": session["id"],
            "session_url": session["url"],
        }
    )
