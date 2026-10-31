from datetime import timedelta

from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from products.models import Product, ProductViewHistory, FlashSale
from products.permissions import IsStaffOrReadOnly


class FlashSaleListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsStaffOrReadOnly]
    queryset = FlashSale.objects.order_by('start_time')

    class FlashSaleSerializer(serializers.ModelSerializer):
        class Meta:
            model = FlashSale
            fields = ('id', 'product', 'discount_percentage', 'start_time', 'end_time')

        def validate_discount_percentage(self, value):
            if not 1 <= value <= 100:
                raise serializers.ValidationError("Discount must be between 1 and 100.")
            return value

        def validate(self, attrs):
            if attrs['start_time'] >= attrs['end_time']:
                raise serializers.ValidationError("end_time must be after start_time.")
            return attrs

    serializer_class = FlashSaleSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_flash_sale(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

    # Check if the user has viewed this product before
    user_viewed = ProductViewHistory.objects.filter(user=request.user, product=product).exists()

    # Check if the product is or will be on a flash sale within the next 24 hours
    now = timezone.now()
    upcoming_flash_sale = FlashSale.objects.filter(
        product=product,
        start_time__lte=now + timedelta(hours=24),
        end_time__gte=now,
    ).first()

    if user_viewed and upcoming_flash_sale:
        discount = upcoming_flash_sale.discount_percentage
        start_time = upcoming_flash_sale.start_time
        end_time = upcoming_flash_sale.end_time
        return Response({
            "message": f"This product will be on a {discount}% off flash sale!",
            "start_time": start_time,
            "end_time": end_time
        })
    else:
        return Response({
            "message": "No upcoming flash sales for this product."
        })
