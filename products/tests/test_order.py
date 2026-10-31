from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from products.models import Product, Order

User = get_user_model()


class OrderTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(phone_number='+998901234567', password='testpass')
        self.other_user = User.objects.create_user(phone_number='+998901112233', password='testpass')
        self.product = Product.objects.create(name='Laptop', description='Laptop', price=100, stock=5)

    def test_anonymous_cannot_create_order(self):
        response = self.client.post(reverse('order-list'), {'product': self.product.id, 'quantity': 1})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_reduces_stock_and_sets_customer(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('order-list'), {'product': self.product.id, 'quantity': 2})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['customer'], self.user.id)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_cannot_order_more_than_stock(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('order-list'), {'product': self.product.id, 'quantity': 10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_product_returns_400(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('order-list'), {'quantity': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_order_adjusts_stock(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('order-list'), {'product': self.product.id, 'quantity': 2})
        url = reverse('order-detail', args=[response.data['id']])
        response = self.client.patch(url, {'quantity': 4})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)

    def test_user_sees_only_own_orders(self):
        Order.objects.create(product=self.product, customer=self.other_user, quantity=1)
        own = Order.objects.create(product=self.product, customer=self.user, quantity=1)
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('order-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([o['id'] for o in response.data['results']], [own.id])

    def test_user_cannot_delete_foreign_order(self):
        order = Order.objects.create(product=self.product, customer=self.other_user, quantity=1)
        self.client.force_authenticate(self.user)
        response = self.client.delete(reverse('order-detail', args=[order.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_status_transition_validation(self):
        order = Order.objects.create(product=self.product, customer=self.user, quantity=1)
        order.set_status(Order.PROCESSING)
        with self.assertRaises(ValueError):
            order.set_status(Order.PENDING)
