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

يتضمن `docker-compose.yml` كذلك Evolution API v2.3.7 بواجهة Manager المدمجة، وPostgreSQL وRedis. خطوات التشغيل والربط بالـIP الحالي موجودة في [VPS_DEPLOYMENT.md](VPS_DEPLOYMENT.md).

1. يحتوي مجلد العمل الحالي على `.env` مولّدًا ومربوطًا بالـIP. عند النشر عبر Git انقله إلى الخادم بقناة آمنة لأنه مستبعد من المستودع. ولإنشاء إعداد جديد بدلًا منه:
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
   - الإعداد الحالي `MEMO_BIND_IP=0.0.0.0` يجعل المتجر متاحًا على `http://179.198.215.77:8001`.
4. تحقّق من حالة الحاويات والسجلات:
   ```bash
   docker compose ps
   docker compose logs --tail=100 web nginx
   ```

## الإنتاج العادي (بدون Docker)

انسخ `.env.example` إلى `.env` واضبط `SECRET_KEY` و`PUBLIC_ORIGIN` وإعدادات SMTP. يستنتج التطبيق `ALLOWED_HOSTS` و`CSRF_TRUSTED_ORIGINS` وإعدادات HTTPS من `PUBLIC_ORIGIN`. استخدم `config.settings.production`، شغّل `optimize_images` بعد رفع صور جديدة ثم `collectstatic`، وقدّم `/media/` من object storage أو خادم وسائط موثوق. طبقة الدفع في `apps/checkout/services.py` abstraction بلا مفاتيح وهمية.

## التحقق

```powershell
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
```

قبل الإنتاج أنشئ قيمًا عشوائية مختلفة لـ`SECRET_KEY` و`EVOLUTION_API_KEY` و`EVOLUTION_WEBHOOK_SECRET` و`EVOLUTION_DB_PASSWORD` (لا تنسخ ناتجًا حقيقيًا إلى Git):

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## تأكيد الطلبات عبر WhatsApp (Evolution API v2)

القيم الداخلية لـEvolution موجودة في `.env`، ويُنشأ instance باسم `memo-store` تلقائيًا في أول تشغيل. عند ضبط `EVOLUTION_AUTO_CONFIGURE_WEBHOOK=1` تهيئ حاوية التطبيق webhook الخاص بالـinstance تلقائيًا، ويمكن تنفيذ العملية يدويًا أيضًا:

```powershell
python manage.py migrate
python manage.py configure_evolution_webhook
python manage.py test apps.checkout apps.orders
```

يُضبط Evolution API لإرسال حدث `MESSAGES_UPSERT` عبر شبكة Docker الداخلية إلى:

```text
http://nginx/api/whatsapp/webhook/
```

أمر الإعداد يفعّل `MESSAGES_UPSERT` فقط، يعطّل `byEvents`، ويرسل header باسم `X-Webhook-Secret` وقيمته المطابقة لـ`EVOLUTION_WEBHOOK_SECRET`. لا تضع السر في query string.

بعد إنشاء الطلب تصبح حالته `pending_confirmation`. يرسل Django التفاصيل بعد نجاح transaction. الوضع الموثوق هو رسالة نصية تطلب الرد بـ`1` للتأكيد أو `2` للتعديل أو `3` للإلغاء. عند وجود أكثر من طلب معلّق لنفس الرقم يُطبّق الرد المختصر على أحدث طلب، ويمكن تحديد طلب بعينه بإرسال الرقم ثم رقم الطلب، مثل `1 MEMO-XXXXXXXX`.
