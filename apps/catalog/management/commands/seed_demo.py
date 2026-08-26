from datetime import timedelta
from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.catalog.models import Category, Collection, Color, Product, ProductImage, ProductVariant, Size
from apps.orders.models import Coupon

class Command(BaseCommand):
    help = "Create isolated MEMO demo catalog, variants, coupon, and dashboard user."
    def handle(self, *args, **options):
        categories = []
        category_data = [(1,"رجالي","men","memo-black-tee-logo-v3.png"),(2,"نسائي","women","memo-sand-hoodie-logo-v3.png"),(3,"Unisex","unisex","memo-white-tee-logo-v3.png"),(4,"Oversized","oversized","memo-gray-sweat-logo-v3.png"),(5,"T-Shirts","t-shirts","memo-black-tee-logo-v3.png"),(6,"Hoodies","hoodies","memo-sand-hoodie-logo-v3.png")]
        for order, name, slug, image_name in category_data:
            category, _ = Category.objects.update_or_create(slug=slug, defaults={"name":name,"sort_order":order,"is_active":True,"image":f"categories/{image_name}","description":"قطع معاصرة بقَصّات واثقة وخامات مختارة."})
            categories.append(category)
        collection, _ = Collection.objects.update_or_create(slug="drop-01", defaults={"name":"DROP 01","description":"الإصدار الأول من MEMO.","cover_image":"collections/memo-drop-01.png","hero_image":"collections/memo-drop-01.png","is_active":True})
        colors = [Color.objects.update_or_create(slug=slug, defaults={"name":name,"hex_code":hex_code,"sort_order":i})[0] for i,(name,slug,hex_code) in enumerate([("أسود","black","#101010"),("عاجي","ivory","#E8DFD0"),("رملي","sand","#B7A185")])]
        sizes = [Size.objects.update_or_create(slug=s.lower(), defaults={"name":s,"sort_order":i})[0] for i,s in enumerate(["S","M","L","XL"])]
        products = [
            ("تيشيرت Essential الأسود","essential-black-tee","MEMO-TS-001",790,990,0),
            ("هودي Form العاجي","form-ivory-hoodie","MEMO-HD-002",1390,None,1),
            ("تيشيرت Structure الرملي","structure-sand-tee","MEMO-TS-003",890,None,2),
            ("سويتشيرت Signature الأسود","signature-black-sweatshirt","MEMO-SW-004",1290,1490,0),
            ("تيشيرت Quiet الأبيض","quiet-ivory-tee","MEMO-TS-005",760,None,1),
            ("هودي After Dark","after-dark-hoodie","MEMO-HD-006",1490,None,0),
            ("قميص Canvas واسع","canvas-overshirt","MEMO-OS-007",1690,1890,2),
            ("بنطال Line الأسود","line-black-trouser","MEMO-TR-008",1450,None,0),
        ]
        catalog_images = ["memo-black-tee-logo-v3.png", "memo-sand-hoodie-logo-v3.png", "memo-white-tee-logo-v3.png", "memo-gray-sweat-logo-v3.png"]
        for idx,(name,slug,sku,price,compare,color_idx) in enumerate(products):
            product,_ = Product.objects.update_or_create(slug=slug, defaults={"name":name,"base_sku":sku,"short_description":"قَصّة معاصرة وخامة ثقيلة بانسيابية مدروسة.","description":"قطعة يومية صُممت حول راحة الحركة ووضوح القَصّة. تفاصيل قليلة، محسوبة، وحضور يبقى.","material":"قطن ثقيل فاخر 100%.","care_instructions":"غسيل بارد مع ألوان مشابهة. تجفيف طبيعي.","price":price,"compare_at_price":compare,"category":categories[idx%len(categories)],"status":"active","featured":idx<4,"new_arrival":idx<5,"bestseller":idx in [0,1,3,5]})
            product.collections.add(collection)
            ProductImage.objects.update_or_create(product=product, sort_order=0, defaults={"image":f"products/{catalog_images[idx % len(catalog_images)]}","alt_text":f"{name} — إطلالة MEMO","is_primary":True})
            color=colors[color_idx]
            for size_idx,size in enumerate(sizes):
                stock = 0 if (idx+size_idx)%7==0 else (2 if (idx+size_idx)%5==0 else 9+size_idx)
                ProductVariant.objects.update_or_create(product=product,color=color,size=size,defaults={"sku":f"{sku}-{color.slug.upper()}-{size.name}","stock_quantity":stock,"is_active":True,"low_stock_threshold":3})
        Coupon.objects.update_or_create(code="MEMO10", defaults={"discount_type":"percentage","value":10,"min_order":1000,"max_discount":300,"starts_at":timezone.now()-timedelta(days=1),"ends_at":timezone.now()+timedelta(days=90),"usage_limit":500,"per_user_limit":1,"is_active":True})
        group,_=Group.objects.get_or_create(name="Owner")
        permissions=Permission.objects.filter(codename__in=["manage_orders","view_product","add_product","change_product","view_productvariant","change_productvariant","view_order","change_order"])
        group.permissions.set(permissions)
        user,created=User.objects.get_or_create(username="memo_owner",defaults={"email":"owner@memo.local","first_name":"MEMO","is_staff":True})
        if created: user.set_password("ChangeMe123!"); user.save()
        user.groups.add(group)
        self.stdout.write(self.style.SUCCESS("Demo ready: memo_owner / ChangeMe123! — change it after first login. Coupon: MEMO10"))
