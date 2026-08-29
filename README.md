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

## الإنتاج

انسخ `.env.example` إلى `.env` واضبط `SECRET_KEY` و`ALLOWED_HOSTS` و`CSRF_TRUSTED_ORIGINS` وإعدادات SMTP. استخدم `config.settings.production`، شغّل `optimize_images` بعد رفع صور جديدة ثم `collectstatic`، وقدّم `/media/` من object storage أو خادم وسائط موثوق. طبقة الدفع في `apps/checkout/services.py` abstraction بلا مفاتيح وهمية.

## التحقق

```powershell
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
```
