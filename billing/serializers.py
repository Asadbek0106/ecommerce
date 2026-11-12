from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class ChargeSerializer(serializers.Serializer):
    payment_method = serializers.CharField(help_text="Stripe PaymentMethod ID, test uchun: pm_card_visa")
    order_id = serializers.IntegerField(help_text="To'lanadigan buyurtma ID si")
