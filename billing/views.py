from decimal import Decimal

import stripe
from django.conf import settings
from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from products.models import Order
from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateChargeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        stripe_token = request.data.get("stripe_token")
        order_id = request.data.get("order_id")

        if not stripe_token or not order_id:
            return Response({"error": "stripe_token and order_id are required"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.select_related('product').get(id=order_id, customer=request.user)
        except (Order.DoesNotExist, ValueError):
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.is_paid:
            return Response({"error": "Order is already paid"}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = order.product.price * order.quantity
        try:
            charge = stripe.Charge.create(
                amount=int(total_amount * Decimal(100)),
                currency="usd",
                source=stripe_token,
            )
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        Payment.objects.create(
            order=order,
            stripe_charge_id=charge["id"],
            amount=total_amount
        )

        order.is_paid = True
        order.save(update_fields=['is_paid'])

        return Response({"status": "Payment successful"}, status=status.HTTP_200_OK)
