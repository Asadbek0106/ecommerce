from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from products.models import Order
from products.models import Review, Category
from products.permissions import IsOwnerOrReadOnly
from products.serializers import OrderSerializer
from products.serializers import ReviewSerializer, CategorySerializer


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    owner_field = 'customer'
    queryset = Order.objects.select_related('product', 'customer').order_by('-created_at')
    serializer_class = OrderSerializer

    def get_queryset(self):
        # Staff sees all orders, regular users see only their own
        queryset = super().get_queryset()
        if getattr(self, 'swagger_fake_view', False):
            return queryset.none()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(customer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    queryset = Review.objects.order_by('-date_posted')
    serializer_class = ReviewSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]  # default =  AllowAny

    queryset = Category.objects.order_by('id')
    serializer_class = CategorySerializer
