from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from products.models import Product


@swagger_auto_schema(method='post', operation_description="Admin replenishes stock for a product")
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_replenish_stock(request, product_id, amount):
    if amount <= 0:
        return Response({'status': 'error', 'message': 'Amount must be positive'},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'status': 'error', 'message': 'Product does not exist'},
                        status=status.HTTP_404_NOT_FOUND)

    product.increase_stock(amount)
    return Response({'status': 'success', 'message': f'Successfully replenished stock by {amount}'})
