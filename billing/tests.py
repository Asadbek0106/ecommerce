from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from billing.models import Payment
from products.models import Order, Product

User = get_user_model()


class CreateChargeTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(phone_number='+998901234567', password='testpass')
        self.other_user = User.objects.create_user(phone_number='+998901112233', password='testpass')
        product = Product.objects.create(name='Book', description='Book', price=10, stock=5)
        self.order = Order.objects.create(product=product, customer=self.user, quantity=2)
        self.url = reverse('create-charge')

    def test_anonymous_cannot_pay(self):
        response = self.client.post(self.url, {'payment_method': 'pm_card_visa', 'order_id': self.order.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_pay_foreign_order(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(self.url, {'payment_method': 'pm_card_visa', 'order_id': self.order.id})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @mock.patch('billing.views.stripe.PaymentIntent.create', return_value={'id': 'pi_test', 'status': 'succeeded'})
    def test_successful_payment(self, charge_create):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, {'payment_method': 'pm_card_visa', 'order_id': self.order.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        charge_create.assert_called_once()
        kwargs = charge_create.call_args.kwargs
        self.assertEqual(kwargs['amount'], 2000)
        self.assertEqual(kwargs['payment_method'], 'pm_card_visa')
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_paid)
        self.assertEqual(Payment.objects.get().stripe_charge_id, 'pi_test')

        # Paying the same order twice is rejected
        response = self.client.post(self.url, {'payment_method': 'pm_card_visa', 'order_id': self.order.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
