# نقل بيانات MEMO من SQLite إلى PostgreSQL

الإعداد الجديد يستخدم PostgreSQL للإنتاج. لا تحذف volume القديم `memo_db_data` قبل التحقق من البيانات المنقولة. خذ نسخة احتياطية من قاعدة SQLite ووسائط `memo_media_data` أولًا، وأوقف استقبال الطلبات أثناء النقل حتى لا تفقد طلبات جديدة.

1. أضف `POSTGRES_DB` و`POSTGRES_USER` و`POSTGRES_PASSWORD` و`POSTGRES_HOST=postgres` إلى ملف `.env` على الخادم. استخدم كلمة مرور عشوائية طويلة.
2. ابنِ صورة التطبيق الجديدة ثم شغّل PostgreSQL فقط: `docker compose build web notifications` ثم `docker compose up -d postgres`.
3. صدّر قاعدة SQLite القديمة إلى ملف داخل volume القديم، بعد تطبيق الهجرة الجديدة عليه:

   ```bash
   docker compose run --rm --no-deps \
     -e DJANGO_SETTINGS_MODULE=config.settings.development \
     -e DB_PATH=/app/data/db.sqlite3 \
     -v memo_db_data:/app/data \
     --entrypoint sh web -c 'python manage.py migrate --noinput && python manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission --indent 2 --output /app/data/memo-export.json'
   ```

4. أنشئ جداول PostgreSQL ثم حمّل البيانات:

   ```bash
   docker compose run --rm --no-deps --entrypoint python web manage.py migrate --noinput
   docker compose run --rm --no-deps -v memo_db_data:/app/legacy --entrypoint python web manage.py loaddata /app/legacy/memo-export.json
   ```

5. قارن عدد الطلبات والمنتجات والمستخدمين بين القاعدتين، ثم شغّل الخدمات: `docker compose up -d --build web notifications nginx`.

الطلبات القديمة لا تملك رابط `OrderItem.variant` الجديد. عند إلغائها، يحاول النظام إيجاد المتغير بواسطة SKU المحفوظ في الطلب، ويسجل خطأ إذا لم يجده. راجع سجلات التطبيق بعد الإلغاء القديم.
