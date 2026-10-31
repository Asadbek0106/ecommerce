from unittest import mock

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class SMSLoginTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.phone = '+998901234567'

    @mock.patch('custom_auth.views.requests.post')
    def test_send_and_verify_sms(self, post):
        post.return_value.status_code = 200
        response = self.client.post(reverse('send_sms'), {'phone_number': self.phone})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        code = cache.get(f'sms_code:{self.phone}')
        data = {'phone_number': self.phone, 'verification_code': code}
        response = self.client.post(reverse('verify_sms'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

        # The code is single use
        response = self.client.post(reverse('verify_sms'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_code(self):
        data = {'phone_number': self.phone, 'verification_code': '000000'}
        response = self.client.post(reverse('verify_sms'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
