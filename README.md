# MEMO — Premium Arabic Fashion E-commerce

متجر Django عربي RTL بواجهة editorial، catalog وvariants حقيقية، session cart، coupons، guest checkout، order snapshots، حسابات، wishlist، ولوحة تشغيل مخصصة بصلاحيات server-side.

## التشغيل المحلي

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py optimize_images
python manage.py runserver
```

افتح `http://127.0.0.1:8000/`. بيانات العرض: `memo_owner` / `ChangeMe123!`، وكود الخصم `MEMO10`. غيّر كلمة المرور فور أول دخول.

## التشغيل عبر Docker (على سيرفر Hostinger VPS KVM 2)

تم تجهيز المشروع بحاوية تطبيق وحاوية Nginx مهيأة لخدمة الملفات الثابتة والوسائط، مع إمكانية استضافة مواقع أخرى على نفس السيرفر:

1. انسخ `.env.example` إلى `.env` واضبط بياناتك:
   ```bash
   cp .env.example .env
   nano .env
   ```
2. ابنِ وشغّل الحاويات:
   ```bash
   docker compose up -d --build
   ```
3. تم ضبط المنفذ الافتراضي على `8001` (`MEMO_PORT=8001`) لمنع تعارض البورتات مع أي مواقع أخرى على نفس السيرفر:
   - للربط مع Nginx الرئيسي على السيرفر لتفعيل SSL/Let's Encrypt وتوجيه الدومين، وجه `proxy_pass http://127.0.0.1:8001;`.
   - إذا كان هذا هو الموقع الوحيد وتريد ربطه بالبورت 80 مباشرة دون بروكسي خارجي، عدّل في `.env`: `MEMO_PORT=80`.

## الإنتاج العادي (بدون Docker)

انسخ `.env.example` إلى `.env` واضبط `SECRET_KEY` و`ALLOWED_HOSTS` و`CSRF_TRUSTED_ORIGINS` وإعدادات SMTP. استخدم `config.settings.production`، شغّل `optimize_images` بعد رفع صور جديدة ثم `collectstatic`، وقدّم `/media/` من object storage أو خادم وسائط موثوق. طبقة الدفع في `apps/checkout/services.py` abstraction بلا مفاتيح وهمية.

## التحقق

```powershell
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
```

## تأكيد الطلبات عبر WhatsApp (Evolution API v2)

أضف قيم `EVOLUTION_API_URL` و`EVOLUTION_API_KEY` و`EVOLUTION_INSTANCE` و`EVOLUTION_WEBHOOK_SECRET` إلى ملف `.env`، ثم نفّذ:

```powershell
python manage.py migrate
python manage.py test apps.checkout apps.orders
```

اضبط Evolution API لإرسال حدث `MESSAGES_UPSERT` إلى:

```text
https://your-store.example/api/whatsapp/webhook/
```

يجب أن يصل الطلب مع header باسم `X-Webhook-Secret` وقيمته المطابقة لـ`EVOLUTION_WEBHOOK_SECRET`. إذا كانت نسخة Evolution أو إعداد الـwebhook لا يدعم إضافة header مخصص، أضفه في reverse proxy موثوق أمام Django؛ لا تضع السر في query string. عطّل خيار `webhook_by_events` أو تأكد أن عنوان الحدث النهائي ما زال يطابق المسار أعلاه.

بعد إنشاء الطلب تصبح حالته `pending_confirmation`. يرسل Django التفاصيل وأزرار التأكيد والإلغاء بعد نجاح transaction، ثم يستخدم رسالة `1`/`2` بديلة إذا لم تدعم القناة الأزرار. لا يعالج الرد الرقمي إلا عندما يوجد طلب معلّق واحد فقط لنفس رقم WhatsApp.
