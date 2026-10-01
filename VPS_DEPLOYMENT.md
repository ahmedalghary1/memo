# نشر MEMO وEvolution على الـVPS

## العناوين الحالية

- المتجر: `http://179.198.215.77:8001`
- Evolution API: داخلي، ومتاح محليًا على الخادم في `127.0.0.1:8080`
- Evolution Manager المدمج: `http://127.0.0.1:8080/manager`

المتغير الوحيد الذي يمثل عنوان المتجر العام هو `PUBLIC_ORIGIN` داخل `.env`. عند ربط الدومين وSSL غيّره من:

```env
PUBLIC_ORIGIN=http://179.198.215.77:8001
```

إلى:

```env
PUBLIC_ORIGIN=https://yourdomain.com
```

لا تغيّر `EVOLUTION_API_URL` أو `EVOLUTION_WEBHOOK_URL`؛ كلاهما يستخدم شبكة Docker الداخلية.

## التشغيل الأول

على الخادم، من مجلد المشروع:

```bash
chmod 600 .env
docker compose pull
docker compose up -d --build
docker compose ps
docker compose logs --tail=150 evolution web nginx
```

في التشغيل الأول ينشئ التطبيق Evolution instance باسم `memo-store` ويضبط الـwebhook تلقائيًا. قد يستغرق PostgreSQL وEvolution دقيقة أو دقيقتين قبل أن تصبح كل الحاويات `healthy`.

إذا كان UFW مفعّلًا، افتح منفذ المتجر فقط. لا تفتح منافذ Evolution أو Manager لأنها مربوطة بالـloopback:

```bash
sudo ufw allow 8001/tcp
```

## فتح Evolution Manager بأمان

منفذ Evolution مربوط بـ`127.0.0.1` فقط حتى لا ينتقل API key عبر الإنترنت باستخدام HTTP. من جهازك الشخصي افتح SSH tunnel واترك النافذة مفتوحة:

```bash
ssh -N -L 18080:127.0.0.1:8080 YOUR_SSH_USER@179.198.215.77
```

ثم افتح في متصفح جهازك:

```text
http://127.0.0.1:18080/manager
```

داخل Evolution Manager استخدم:

- API URL: `http://127.0.0.1:18080`
- API Key: قيمة `EVOLUTION_API_KEY` من ملف `.env` على الخادم
- Instance: `memo-store`

افتح الـinstance وامسح QR من تطبيق WhatsApp عبر **الأجهزة المرتبطة → ربط جهاز**.

## التحقق

بعد مسح QR:

```bash
docker compose exec web python manage.py configure_evolution_webhook
docker compose logs --tail=100 evolution web
```

أنشئ طلبًا تجريبيًا برقم مصري صحيح. يجب أن تصل رسالة التفاصيل ويستطيع العميل الرد بـ`1` للتأكيد أو `2` للتعديل أو `3` للإلغاء. ولتحديد طلب بعينه عند وجود أكثر من طلب لنفس الرقم، أرسل مثلًا `1 MEMO-XXXXXXXX`.

## القيم التي ما زالت تحتاجها من الخارج

- بيانات دخول SSH للـVPS لرفع المشروع وتشغيل Docker.
- رقم WhatsApp فعّال ومسح QR يدويًا.
- دومين وDNS وشهادة SSL عند الانتقال من الـIP.
- بريد SMTP حقيقي: `EMAIL_HOST_USER` و`EMAIL_HOST_PASSWORD` و`DEFAULT_FROM_EMAIL`.

كل مفاتيح Django وEvolution وقاعدة بيانات Evolution مولّدة بالفعل في `.env` المحلي، والملف مستبعد من Git. انسخه إلى الخادم بطريقة آمنة ولا ترسله في رسالة أو ترفعه إلى مستودع.

## النسخ الاحتياطي

البيانات الدائمة موجودة في Docker volumes التالية:

- `memo_db_data`
- `memo_media_data`
- `memo_evolution_postgres_data`
- `memo_evolution_redis_data`
- `memo_evolution_instances`

يجب تضمينها في خطة النسخ الاحتياطي الدورية.
