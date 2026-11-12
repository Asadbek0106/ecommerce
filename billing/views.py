from decimal import Decimal

import stripe
from django.conf import settings
from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from products.models import Order
from .models import Payment
from .serializers import ChargeSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateChargeView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ChargeSerializer)
    def post(self, request, *args, **kwargs):
        payment_method = request.data.get("payment_method")
        order_id = request.data.get("order_id")

        if not payment_method or not order_id:
            return Response({"error": "payment_method and order_id are required"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.select_related('product').get(id=order_id, customer=request.user)
        except (Order.DoesNotExist, ValueError):
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.is_paid:
            return Response({"error": "Order is already paid"}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = order.product.price * order.quantity
        try:
            # PaymentIntent: Stripe's current API (Charges + card tokens are end-of-life)
            intent = stripe.PaymentIntent.create(
                amount=int(total_amount * Decimal(100)),
                currency="usd",
                payment_method=payment_method,
                confirm=True,
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                metadata={"order_id": order.id},
            )
        except stripe.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if intent["status"] != "succeeded":
            return Response({"error": f"Payment not completed, status: {intent['status']}"},
                            status=status.HTTP_400_BAD_REQUEST)

        Payment.objects.create(
            order=order,
            stripe_charge_id=intent["id"],
            amount=total_amount
        )

        order.is_paid = True
        order.save(update_fields=['is_paid'])

        return Response({"status": "Payment successful", "payment_intent": intent["id"]},
                        status=status.HTTP_200_OK)
