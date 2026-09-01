from datetime import timedelta
from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from apps.catalog.models import Category, Collection, Color, Product, ProductImage, ProductVariant, Size
from apps.orders.models import Coupon

class Command(BaseCommand):
    help = "Create isolated MEMO demo catalog, variants, coupon, and dashboard user."
    def handle(self, *args, **options):
        category_specs = [
            # المستوى الأول
            (1, "رجالي", "men", None, "memo-black-tee-logo-v3.webp"),
            (2, "نسائي", "women", None, "memo-sand-hoodie-logo-v3.webp"),
            (3, "للجميع", "unisex", None, "memo-white-tee-logo-v3.webp"),
            # المستوى الثاني
            (1, "بناطيل", "trousers", "men", "memo-gray-sweat-logo-v3.webp"),
            (2, "قمصان", "shirts", "men", "memo-white-tee-logo-v3.webp"),
            (1, "قطع علوية", "women-tops", "women", "memo-sand-hoodie-logo-v3.webp"),
            (2, "قطع سفلية", "women-bottoms", "women", "memo-gray-sweat-logo-v3.webp"),
            (1, "تيشيرتات", "t-shirts", "unisex", "memo-black-tee-logo-v3.webp"),
            (2, "هوديز", "hoodies", "unisex", "memo-sand-hoodie-logo-v3.webp"),
            (3, "قصّات واسعة", "oversized", "unisex", "memo-gray-sweat-logo-v3.webp"),
            # المستوى الثالث
            (1, "بناطيل جينز", "jeans", "trousers", "memo-black-tee-logo-v3.webp"),
            (2, "بناطيل ترينج", "joggers", "trousers", "memo-gray-sweat-logo-v3.webp"),
            (1, "قمصان كاجوال", "casual-shirts", "shirts", "memo-white-tee-logo-v3.webp"),
            (2, "أوفرشيرت", "overshirts", "shirts", "memo-sand-hoodie-logo-v3.webp"),
            (1, "تيشيرتات نسائي", "women-tshirts", "women-tops", "memo-white-tee-logo-v3.webp"),
            (1, "بناطيل نسائي", "women-pants", "women-bottoms", "memo-sand-hoodie-logo-v3.webp"),
        ]
        categories = {}
        for order, name, slug, parent_slug, image_name in category_specs:
            parent = categories.get(parent_slug)
            category, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "parent": parent,
                    "sort_order": order,
                    "is_active": True,
                    "image": f"categories/{image_name}",
                    "description": "قطع معاصرة بقَصّات واثقة وخامات مختارة.",
                },
            )
            categories[slug] = category
        collection, _ = Collection.objects.update_or_create(slug="drop-01", defaults={"name":"DROP 01","description":"الإصدار الأول من MEMO.","cover_image":"collections/memo-drop-01.png","hero_image":"collections/memo-drop-01.png","is_active":True})
        colors = [Color.objects.update_or_create(slug=slug, defaults={"name":name,"hex_code":hex_code,"sort_order":i})[0] for i,(name,slug,hex_code) in enumerate([("أسود","black","#101010"),("عاجي","ivory","#E8DFD0"),("رملي","sand","#B7A185")])]
        sizes = [Size.objects.update_or_create(slug=s.lower(), defaults={"name":s,"sort_order":i})[0] for i,s in enumerate(["S","M","L","XL"])]
        products = [
            ("تيشيرت Essential الأسود","essential-black-tee","MEMO-TS-001",790,990,0,"t-shirts"),
            ("هودي Form العاجي","form-ivory-hoodie","MEMO-HD-002",1390,None,1,"hoodies"),
            ("تيشيرت Structure الرملي","structure-sand-tee","MEMO-TS-003",890,None,2,"women-tshirts"),
            ("بنطال Jogger Signature الأسود","signature-black-sweatshirt","MEMO-SW-004",1290,1490,0,"joggers"),
            ("تيشيرت Quiet الأبيض","quiet-ivory-tee","MEMO-TS-005",760,None,1,"t-shirts"),
            ("هودي After Dark","after-dark-hoodie","MEMO-HD-006",1490,None,0,"oversized"),
            ("قميص Canvas واسع","canvas-overshirt","MEMO-OS-007",1690,1890,2,"overshirts"),
            ("بنطال Denim Line الأسود","line-black-trouser","MEMO-TR-008",1450,None,0,"jeans"),
        ]
        catalog_images = ["memo-black-tee-logo-v3.webp", "memo-sand-hoodie-logo-v3.webp", "memo-white-tee-logo-v3.webp", "memo-gray-sweat-logo-v3.webp"]
        for idx,(name,slug,sku,price,compare,color_idx,category_slug) in enumerate(products):
            product,_ = Product.objects.update_or_create(slug=slug, defaults={"name":name,"base_sku":sku,"short_description":"قَصّة معاصرة وخامة ثقيلة بانسيابية مدروسة.","description":"قطعة يومية صُممت حول راحة الحركة ووضوح القَصّة. تفاصيل قليلة، محسوبة، وحضور يبقى.","material":"قطن ثقيل فاخر 100%.","care_instructions":"غسيل بارد مع ألوان مشابهة. تجفيف طبيعي.","price":price,"compare_at_price":compare,"category":categories[category_slug],"status":"active","featured":idx<4,"new_arrival":idx<5,"bestseller":idx in [0,1,3,5]})
            product.collections.add(collection)
            ProductImage.objects.update_or_create(product=product, sort_order=0, defaults={"image":f"products/{catalog_images[idx % len(catalog_images)]}","alt_text":f"{name} — إطلالة MEMO","is_primary":True})
            color=colors[color_idx]
            for size_idx,size in enumerate(sizes):
                stock = 0 if (idx+size_idx)%7==0 else (2 if (idx+size_idx)%5==0 else 9+size_idx)
                ProductVariant.objects.update_or_create(product=product,color=color,size=size,defaults={"sku":f"{sku}-{color.slug.upper()}-{size.name}","stock_quantity":stock,"is_active":True,"low_stock_threshold":3})
        Coupon.objects.update_or_create(code="MEMO10", defaults={"discount_type":"percentage","value":10,"min_order":1000,"max_discount":300,"starts_at":timezone.now()-timedelta(days=1),"ends_at":timezone.now()+timedelta(days=90),"usage_limit":500,"per_user_limit":1,"is_active":True})
        group,_=Group.objects.get_or_create(name="Owner")
        permissions=Permission.objects.filter(
            Q(codename="manage_orders") |
            Q(content_type__app_label__in=["catalog", "orders", "marketing", "core"], codename__regex=r"^(add|change|delete|view)_")
        )
        group.permissions.set(permissions)
        user,created=User.objects.get_or_create(username="memo_owner",defaults={"email":"owner@memo.local","first_name":"MEMO","is_staff":True})
        if created: user.set_password("ChangeMe123!"); user.save()
        user.groups.add(group)
        self.stdout.write(self.style.SUCCESS("Demo ready: memo_owner / ChangeMe123! — change it after first login. Coupon: MEMO10"))
