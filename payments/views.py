import os
import stripe
from django.http import HttpResponse

from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import generics, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView

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

    # success_url = "https://www.google.com/"
    # cancel_url = "https://www.bing.com/"


    success_url = request.build_absolute_uri(reverse("payments:payment_success")) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse("payments:payment_cancel"))

    # cancel_url = request.build_absolute_uri(reverse("payment_cancel"))

    # success_url = "http://127.0.0.1:8000/payments/success?session_id={CHECKOUT_SESSION_ID}"
    # cancel_url = "http://127.0.0.1:8000/payments/cancel/"

    # success_url = request.build_absolute_uri(reverse("success"))
    # cancel_url = request.build_absolute_uri(reverse("cancel"))

    if not success_url or not cancel_url:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    session = payment.create_stripe_session(success_url, cancel_url)

    return Response(
        {
            "session_id": session["id"],
            "session_url": session["url"],
        }
    )


@api_view(["POST"])
def payment_success(request):
    session_id = request.GET.get("session_id")
    if session_id:
        stripe.api_key = os.getenv("STRIPE_API_KEY")
        session = stripe.checkout.Session.retrieve(session_id)
        customer = stripe.Customer.retrieve(session.customer)

        return Response({"message": f"Thanks for your payment, {customer.name}!"})
    else:
        return Response({"error": "Session ID not found."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def payment_cancel(request):
    return Response({"message": "Payment can be paid later. The session is available for 24h."})



# class SuccessView(APIView):
#     def get(self, request, *args, **kwargs):
#         session_id = request.GET.get("session_id")
#         try:
#             session = stripe.checkout.Session.retrieve(session_id)
#             if session.payment_status == "paid":
#
#                 return HttpResponse("Payment was successful")
#             else:
#                 return HttpResponse("Payment was unsuccessful")
#         except stripe.error.InvalidRequestError:
#             return HttpResponse("Invalid Session ID")
#
#
# class CancelView(APIView):
#     def get(self, request, *args, **kwargs):
#         return HttpResponse("Payment can be paid later")

