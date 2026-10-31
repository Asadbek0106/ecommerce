from django.db import transaction
from rest_framework import serializers

from products.models import Order, Product


class OrderSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'product', 'customer', 'quantity', 'created_at', 'total_price', 'phone_number', 'is_paid']
        read_only_fields = ['customer', 'is_paid']

    def get_total_price(self, obj):
        return obj.product.price * obj.quantity

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate(self, attrs):
        product = attrs.get('product', getattr(self.instance, 'product', None))
        quantity = attrs.get('quantity', getattr(self.instance, 'quantity', None))
        # On update, the already reserved quantity is returned to stock first
        available = product.stock
        if self.instance is not None and self.instance.product_id == product.id:
            available += self.instance.quantity
        if quantity > available:
            raise serializers.ValidationError({'quantity': "Not enough items in stock."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        product = Product.objects.select_for_update().get(pk=validated_data['product'].pk)
        if not product.reduce_stock(validated_data['quantity']):
            raise serializers.ValidationError({'quantity': "Not enough items in stock."})
        order = Order.objects.create(**validated_data)
        self.send_confirmation_email(order)
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        # Return the old quantity to stock, then reserve the new one
        old_product = Product.objects.select_for_update().get(pk=instance.product_id)
        old_product.increase_stock(instance.quantity)
        new_product = Product.objects.select_for_update().get(
            pk=validated_data.get('product', instance.product).pk
        )
        if not new_product.reduce_stock(validated_data.get('quantity', instance.quantity)):
            raise serializers.ValidationError({'quantity': "Not enough items in stock."})
        return super().update(instance, validated_data)

    def send_confirmation_email(self, order):
        # Here you would send an email. For this example, we'll just print
        print(f"Sent confirmation email for Order {order.id}")
