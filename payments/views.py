from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view
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

    success_url = request.build_absolute_uri(reverse("payments:payment_success")) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse("payments:payment_cancel"))

    if not success_url or not cancel_url:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    session = payment.create_stripe_session(success_url, cancel_url)

    return Response(
        {
            "session_id": session["id"],
            "session_url": session["url"],
        }
    )


@api_view(["GET"])
def payment_success(request):
    session_id = request.GET.get("session_id")
    if session_id:
        payment = Payment.objects.get(stripe_session_id=session_id)
        payment.status = Payment.StatusType.PAID
        payment.save()
        return Response({"message": "Payment was successful!"})
    else:
        return Response({"error": "Session ID not found."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def payment_cancel(request, pk):
    payment = Payment.objects.get(id=pk)
    if payment.status == "PENDING":
        return Response({"message": f"Payment with id: {pk} can be paid later. The session is available for 24h."})
    else:
        return Response({"message": f"Payment with id: {pk} is already paid."})
