# Loyiha tekshiruvi bo'yicha hisobot

**Loyiha:** E-commerce API (Django + DRF)
**Sana:** 2026-yil 31-oktabr
**Natija:** loyiha ishga tushadi, `manage.py check` xatosiz, **25 ta test o'tdi** (oldin 12 ta test bor edi, loyiha esa umuman ishga tushmasdi).

---

## 1. Loyihani ishdan chiqargan jiddiy xatolar

| # | Fayl | Muammo | Tuzatish |
|---|------|--------|----------|
| 1 | `config/urls.py` | `TokenVerifyView` importi o'chirilgan, lekin URL'da ishlatilgan → `NameError`, server umuman ishga tushmasdi | Import qaytarildi |
| 2 | `requirements.txt` | Fayl **UTF-16** kodlashda saqlangan — Linux/Docker/CI'da `pip install -r` ishlamaydi | UTF-8 ga o'tkazildi |
| 3 | `requirements.txt` | `djangorestframework-simplejwt==5.2.2` yangi `setuptools`da yo'q `pkg_resources`ga bog'liq → import xatosi. `stripe` va `redis` paketlari o'rnatilmagan edi | Ishlaydigan va tekshirilgan versiyalar bilan yangilandi; faqat to'g'ridan-to'g'ri kerakli paketlar qoldirildi |
| 4 | `products/fixtures/*.yaml` | Fixture'lar ham UTF-16 da edi | UTF-8 ga o'tkazildi |
| 5 | `products/signals.py`, `models/order.py` | `instance.customer.username` — `CustomUser` modelida `username` maydoni yo'q → **har bir buyurtma yaratilganda `AttributeError`** | `str(customer)` (telefon raqami) ishlatildi |
| 6 | `products/permissions.py` | `IsOwnerOrReadOnly` `obj.owner` ni tekshiradi, `Order` modelida bunday maydon yo'q → buyurtmani tahrirlash/o'chirishda xato | Egasining maydoni view'dan olinadi (`owner_field = 'customer'`), staff'ga ham ruxsat |
| 7 | `config/settings.py` | `SECRET_KEY` faqat `.env`dan olinadi, `.env` bo'lmasa loyiha ishga tushmaydi | Lokal ishlab chiqish uchun standart qiymat qo'shildi (productionda env orqali berilishi kerak) |

## 2. Xavfsizlik kamchiliklari

| Fayl | Muammo | Tuzatish |
|------|--------|----------|
| `products/views/misc.py` (Order) | Har kim (hatto login qilmagan) buyurtma yarata olardi va **barcha foydalanuvchilarning buyurtmalarini** ko'ra olardi; `customer` maydonini client o'zi yuborardi | Faqat autentifikatsiyadan o'tganlar; har kim faqat o'z buyurtmalarini ko'radi (staff — hammasini); `customer` avtomatik `request.user` |
| `billing/views.py` | To'lov endpointi ochiq: istalgan odam istalgan buyurtmani to'lashi, bitta buyurtmani **ikki marta to'lashi** mumkin edi | `IsAuthenticated`, faqat o'z buyurtmasi, qayta to'lov taqiqlandi, faqat `StripeError` ushlanadi |
| `products/services/replenish_stock.py` | `staff_member_required` API uchun mos emas (admin login sahifasiga redirect qiladi), dekoratorlar tartibi noto'g'ri, manfiy `amount` mumkin edi | DRF `IsAdminUser`, musbat miqdor tekshiruvi, to'g'ri swagger dekoratori |
| `products/views/misc.py` (Review) | Sharhni istalgan odam istalgan foydalanuvchi nomidan yozishi/o'chirishi mumkin edi; reyting chegarasiz | Faqat login qilganlar yozadi, `user` avtomatik, faqat egasi o'zgartiradi; reyting 1–5 (yangi migratsiya `0003`) |
| `products/services/product_view_history.py` | Ko'rish tarixini boshqa foydalanuvchi nomidan yozish mumkin edi | `user` avtomatik `request.user`, login majburiy |
| `products/services/flash_sale.py` | Anonim foydalanuvchida `check-sale` 500 xato berardi; aksiyani istalgan odam yarata olardi | Login majburiy; aksiya yaratish faqat staff uchun; chegirma 1–100% va vaqt oralig'i tekshiriladi |
| `custom_auth/views.py` | SMS kod `random` bilan yaratilardi, kod qayta-qayta ishlatilishi mumkin edi, so'rovda timeout yo'q edi | `secrets` moduli, kod bir martalik, `compare_digest`, `timeout=10`, SMS orqali yaratilgan userga `set_unusable_password()` |
| `config/settings.py` | `CSRF_TRUSTED_ORIGINS = ["https://*", "http://*"]`, `DEBUG = True` qattiq yozilgan | Ikkalasi ham env orqali sozlanadi (`DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`) |
| `products/tasks.py` | Telegram `chat_id` kodga qattiq yozilgan | `TELEGRAM_CHAT_ID` env o'zgaruvchisiga ko'chirildi |

## 3. Mantiqiy xatolar

- **Ombor (stock) hisobi:** buyurtma yaratishda stock tranzaksiyasiz kamaytirilardi (bir vaqtdagi so'rovlarda manfiy bo'lishi mumkin edi), buyurtma tahrirlanganda stock umuman o'zgarmasdi. Endi `transaction.atomic` + `select_for_update` ishlatiladi, tahrirlashda eski miqdor qaytarilib, yangisi ayriladi.
- **`validate_quantity`** `product` yuborilmasa `KeyError` (500) berardi → tekshiruv `validate()` ga ko'chirildi, endi 400 qaytadi.
- **`Order.set_status`** ruxsat etilgan o'tishlarni (`is_transition_allowed`) tekshirmasdi → endi tekshiradi.
- **`SIMPLE_JWT`** `SLIDING_TOKEN_*` sozlamalari oddiy tokenlarga ta'sir qilmasdi → `ACCESS_TOKEN_LIFETIME` / `REFRESH_TOKEN_LIFETIME`.
- **Flash sale** tugagan aksiyalarni ham "kelayotgan" deb ko'rsatardi; `datetime.now()` (timezone'siz) → `timezone.now()` va `end_time__gte=now`.
- **Signal** faqat `urls.py` import qilinganda ulanardi → `ProductsConfig.ready()` ga ko'chirildi; Celery vazifasi `transaction.on_commit` orqali yuboriladi; `time.sleep(5)` olib tashlandi.
- **`ProductSerializer`** da `category` maydoni yo'q edi — mahsulotni kategoriya bilan yaratib bo'lmasdi.
- `urls.py` da ikki xil URL bir xil nomga (`product-view-history-create`) ega edi.
- `CustomUser.__str__` `phone_number` bo'sh bo'lsa `None` qaytarib xato berardi.
- Pagination uchun querysetlarga tartib (`order_by`) qo'shildi (`UnorderedObjectListWarning`).

## 4. Kod tozaligi

- `billing/models.py` — takroriy import olib tashlandi; `Payment` admin panelga qo'shildi.
- `ProductViewSet.list` dagi ortiqcha kategoriya filtri olib tashlandi (`ProductFilter` buni allaqachon qiladi); `average_rating` DB `Avg` agregatsiyasi bilan.
- Testlardagi `user_id=1/2` kabi qattiq yozilgan ID'lar va keraksiz importlar tozalandi; kategoriyalar testi pagination javobiga moslashtirildi.

## 5. Infratuzilma

- `Dockerfile`: Python 3.9 → 3.12 (Django 6 talabi), `ENV` sintaksisi yangilandi.
- `docker-compose.yml`: `web` servisida volume `/usr/src/app` ga ulanardi, `WORKDIR` esa `/app` — kod o'zgarishlari konteynerga tushmasdi → `/app`. Eskirgan `version` kaliti olib tashlandi.
- GitHub Actions: `checkout@v4`, `setup-python@v5`, Python 3.12.
- `.gitignore` ga `.idea/` qo'shildi.

## 6. Yangi testlar (13 ta)

- `products/tests/test_order.py` — anonim taqiq, stock kamayishi, stockdan ortiq buyurtma, tahrirlashda stock, faqat o'z buyurtmalari, begona buyurtmani o'chirib bo'lmasligi, status o'tishlari.
- `billing/tests.py` — anonim/begona buyurtma taqiqi, muvaffaqiyatli to'lov (Stripe mock), qayta to'lov taqiqi.
- `custom_auth/tests.py` — SMS yuborish va tasdiqlash (mock), kod bir martalik, noto'g'ri kod.

```
Ran 25 tests ... OK
System check identified no issues (0 silenced).
GET /swagger.json -> 200
```

## 7. Qo'lda e'tibor berish kerak bo'lgan narsalar

- Lokal `.venv` da `simplejwt`, `djangorestframework` yangilandi, `stripe` va `redis` o'rnatildi.
- Serverda `.env` faylida `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `TELEGRAM_CHAT_ID` ni belgilang.
- `data.json` (dumpdata) repoda saqlanmoqda — unda foydalanuvchi parol xeshi (`pbkdf2_sha256$...`) bor, uni repodan olib tashlash tavsiya etiladi.
- Stripe `Charge` API eskirgan; kelajakda `PaymentIntent` ga o'tish tavsiya etiladi.
