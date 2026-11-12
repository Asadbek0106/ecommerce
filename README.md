# E-commerce API

[![CI/CD](https://github.com/xamidjonovk/ecommerce/actions/workflows/django-ci.yml/badge.svg)](https://github.com/xamidjonovk/ecommerce/actions/workflows/django-ci.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Django](https://img.shields.io/badge/django-6.1-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A REST API for an online store built with **Django** and **Django REST Framework**.
It covers the product catalog, orders with stock control, reviews, flash sales,
phone-number login via SMS, Stripe payments and Telegram notifications for new orders.

---

## Contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [API overview](#api-overview)
- [Testing](#testing)
- [CI/CD](#cicd)
- [License](#license)

## Features

- **Catalog**: products and categories with filtering (category, price range), search,
  pagination, related products, top-rated products and average rating.
- **Orders**: users see and manage only their own orders. Stock is reserved inside a
  database transaction (`select_for_update`), so concurrent orders cannot oversell.
  Order status changes follow allowed transitions only.
- **Reviews**: rating from 1 to 5, editable only by the author.
- **Flash sales**: staff create time-limited discounts; users can check upcoming sales
  for products they have viewed.
- **Authentication**: JWT (SimpleJWT), Djoser user endpoints, and passwordless login
  with a one-time SMS code (Infobip).
- **Payments**: Stripe PaymentIntents; an order can only be paid once, and only by its owner.
- **Notifications**: a Celery task sends new orders to a Telegram chat.
- **Documentation**: interactive Swagger UI and ReDoc.

## Tech stack

| Area | Tools |
|------|-------|
| Framework | Django 6.1, Django REST Framework 3.18 |
| Auth | djangorestframework-simplejwt, Djoser |
| Background jobs | Celery, RabbitMQ (broker), Redis (results) |
| Payments | Stripe |
| Docs | drf-yasg (Swagger / ReDoc) |
| Database | SQLite (default) |
| DevOps | Docker, Docker Compose, GitHub Actions, GitHub Container Registry |

## Project structure

```
ecommerce/
├── config/          # settings, root URLs, Celery app
├── products/        # catalog, orders, reviews, flash sales
│   ├── models/
│   ├── serializers/
│   ├── services/    # flash sale, view history, stock replenishment
│   ├── views/
│   ├── fixtures/
│   └── tests/
├── custom_auth/     # phone-number user model, SMS login
├── billing/         # Stripe payments
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Getting started

### Requirements

- Python 3.12 or newer
- Optional: Docker and Docker Compose

### Run locally

```bash
git clone https://github.com/xamidjonovk/ecommerce.git
cd ecommerce

python -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # asks for a phone number instead of a username
python manage.py runserver
```

Open http://127.0.0.1:8000/ for the Swagger UI.

Optional sample categories:

```bash
python manage.py loaddata categories
```

By default Celery tasks run synchronously (`CELERY_TASK_ALWAYS_EAGER=True`),
so RabbitMQ and Redis are not needed for local development.

### Run with Docker Compose

```bash
docker compose up --build
```

This starts the API on http://localhost:8001/, a Celery worker, RabbitMQ
(management UI on http://localhost:15672/, `guest` / `guest`) and Redis.
Migrations are applied automatically.

```bash
docker compose exec web python manage.py createsuperuser
```

## Configuration

Settings are read from environment variables or from a `.env` file in the project root.
Every variable is optional for local development.

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key. **Required in production.** | insecure dev key |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated host names | `*` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated origins, e.g. `https://shop.example.com` | empty |
| `CELERY_TASK_ALWAYS_EAGER` | Run Celery tasks in-process instead of via a broker | `True` |
| `CELERY_BROKER_URL` | Broker URL, e.g. `amqp://guest:guest@localhost:5672//` | — |
| `CELERY_RESULT_BACKEND` | Result backend, e.g. `redis://localhost:6379/0` | — |
| `STRIPE_PUBLIC_KEY` / `STRIPE_SECRET_KEY` | Stripe API keys | — |
| `SMS_KEY` | Infobip API key for SMS login | — |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Telegram bot and chat for order notifications | — |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP credentials for Djoser emails | — |

Example `.env`:

```env
SECRET_KEY=change-me
DEBUG=False
ALLOWED_HOSTS=api.example.com
STRIPE_SECRET_KEY=sk_test_...
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=123456789
```

## API overview

All endpoints are prefixed with `/api/v1/`. Full, interactive documentation is
available at `/` (Swagger) and `/redoc/`.

Authenticated requests use the header `Authorization: Bearer <access_token>`.

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `custom_auth/token/` | Get access and refresh tokens (phone number + password) |
| POST | `custom_auth/token/refresh/` | Refresh the access token |
| POST | `custom_auth/token/verify/` | Verify a token |
| POST | `sms-auth/send-sms/` | Send a one-time login code |
| POST | `sms-auth/verify-sms/` | Exchange the code for JWT tokens |
| — | `custom_auth/users/...` | Djoser user management (register, me, password reset) |

### Catalog

| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `products/` | Public. Filters: `category`, `min_price`, `max_price`, `search` |
| GET | `products/{id}/` | Public. Includes related products |
| GET | `products/top_rated/` | Public |
| GET | `products/{id}/average_rating/` | Public |
| POST / PUT / DELETE | `products/`, `products/{id}/` | Staff |
| CRUD | `categories/` | Authenticated |
| CRUD | `reviews/` | Read: public. Write: authenticated, edit: author only |

### Orders and payments

| Method | Endpoint | Access |
|--------|----------|--------|
| CRUD | `orders/` | Authenticated, own orders only (staff see all) |
| POST | `pay/` | Pay your own order: `{"order_id": 1, "payment_method": "pm_card_visa"}` |
| POST | `admin/replenish_stock/{product_id}/{amount}/` | Staff |

### Flash sales and views

| Method | Endpoint | Access |
|--------|----------|--------|
| GET / POST | `sale/` | Read: public. Create: staff |
| GET | `check-sale/{product_id}/` | Authenticated |
| POST | `product-view/` | Authenticated |

## Testing

```bash
python manage.py test
```

The suite covers products, categories, orders (permissions, stock, status transitions),
payments (Stripe is mocked) and SMS login (the SMS gateway is mocked).
No external services are needed to run it.

## CI/CD

GitHub Actions workflow: [`.github/workflows/django-ci.yml`](.github/workflows/django-ci.yml)

| Job | Runs on | What it does |
|-----|---------|--------------|
| **test** | every push and pull request to `main` | Python 3.12 and 3.13: `manage.py check`, missing-migration check, full test suite |
| **docker** | after `test` passes | Builds the Docker image. On pushes to `main` it also publishes it to GitHub Container Registry as `ghcr.io/<owner>/ecommerce:latest` and `:sha-<commit>` |

No repository secrets are required for CI. If `SECRET_KEY` is set as a secret it is used;
otherwise a development key is used for the test run.

Pull the published image:

```bash
docker pull ghcr.io/xamidjonovk/ecommerce:latest
```

## License

Distributed under the MIT License. See [LICENSE](LICENSE).
