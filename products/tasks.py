import requests
from django.conf import settings
from celery import shared_task


@shared_task
def send_telegram_notification(order_id, product_name, quantity, customer_username, phone_number):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return None

    method = 'sendMessage'
    message_text = f"New Order: {order_id}\n Product: {product_name}\n Quantity: {quantity}\n " \
                   f"Client: {customer_username}\n tel: {phone_number}"

    response = requests.post(
        url=f'https://api.telegram.org/bot{token}/{method}',
        data={'chat_id': chat_id, 'text': message_text},
        timeout=10,
    )
    return response.json()
