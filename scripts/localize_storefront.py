"""Apply the reviewed English storefront copy to templates (dashboard excluded)."""

from pathlib import Path


TRANSLATIONS = dict(
    line.split("|", 1)
    for line in """
حسابي|My account
طلباتي|My orders
البيانات الشخصية|Personal details
العناوين|Addresses
المفضلة|Wishlist
تغيير كلمة المرور|Change password
تسجيل الخروج|Log out
مرحبًا،|Welcome,
تابع طلباتك وعناوينك والقطع التي حفظتها من مكان واحد.|Manage your orders, addresses, and saved pieces in one place.
إجمالي الطلبات|Total orders
طلباتك|Your orders
ابدأ التسوق|Start shopping
لا توجد طلبات بعد.|No orders yet.
ستظهر طلباتك هنا فور إتمام أول شراء.|Your orders will appear here after your first purchase.
صفحات الطلبات|Order pages
من |of 
تسجيل الدخول|Log in
مرحبًا|Welcome
بعودتك.|back.
طلباتك، عناوينك، والقطع التي حفظتها في مكان واحد.|Your orders, addresses, and saved pieces in one place.
دخول|Log in
نسيت كلمة المرور؟|Forgot your password?
جديد هنا؟|New here?
أنشئ حسابًا|Create an account
العودة إلى طلباتي|Back to my orders
تحديثات الطلب|Order updates
تم استلام الطلب، وسيظهر أول تحديث هنا بعد مراجعته.|We have received your order. Its first update will appear here after review.
التوصيل|Delivery
المجموع|Subtotal
الشحن|Shipping
الإجمالي|Total
تحتاج مساعدة؟|Need help?
الأمان|Security
كلمة مرور|Password
أقوى.|stronger.
حفظ التغيير|Save changes
تم التحديث.|Updated.
جديدة.|new.
حفظ|Save
تحقق من بريدك.|Check your email.
إن كان البريد مسجلًا، ستصلك رسالة الاستعادة خلال دقائق.|If the email is registered, you will receive a reset link within minutes.
استعادة|Restore
الدخول.|access.
أدخل بريدك وسنرسل تعليمات الاستعادة.|Enter your email and we will send reset instructions.
إرسال|Send
بياناتي|My details
بياناتك.|Your details.
الطلبات|Orders
المحفوظات|Saved items
الملف والعناوين|Profile and addresses
الملف الشخصي|Profile
حفظ البيانات|Save details
عناوين التوصيل|Delivery addresses
إلغاء التعديل|Cancel editing
الافتراضي|Default
، مبنى |, building 
هل تريد حذف هذا العنوان؟|Delete this address?
تعديل العنوان|Edit address
إضافة عنوان|Add address
حفظ العنوان|Save address
تعديل|Edit
حذف|Delete
لا توجد عناوين محفوظة بعد.|No saved addresses yet.
أضف عنوانًا لتسريع طلباتك القادمة.|Add an address to make your next checkout faster.
حساب جديد|New account
ابقَ|Stay
أقرب.|closer.
تابع طلباتك واحفظ اختياراتك واعرف بالإصدارات أولًا.|Track orders, save your favorites, and hear about new releases first.
إنشاء حساب|Create an account
إنشاء الحساب|Create account
لديك حساب؟|Already have an account?
سجّل الدخول|Log in
اختر اللون والمقاس قبل إضافة القطعة إلى السلة.|Choose a color and size before adding an item to your bag.
الخيارات المتاحة|Available options
اختر قبل الإضافة|Choose an option
متبقي|Only
إضافة إلى السلة|Add to bag
إزالة|Remove
لا توجد قطع محفوظة.|No saved items yet.
احفظ ما يلفت نظرك وارجع إليه في أي وقت.|Save pieces you love and revisit them anytime.
اكتشف القطع|Explore pieces
قطع يومية. حضور غير عادي.|Everyday pieces. Distinct presence.
للأزياء المعاصرة|Contemporary fashion
تصميم هادئ، حضور لا يُنسى.|Quiet design. Lasting presence.
أزياء معاصرة|Contemporary fashion
قطع يومية بقصّات معاصرة وخامات مختارة.|Everyday pieces with modern cuts and selected fabrics.
انتقل إلى المحتوى|Skip to content
إغلاق الفلاتر|Close filters
العودة إلى أعلى الصفحة|Back to top
العودة للحقيبة|Back to bag
لا تحتاج إلى إنشاء حساب. أدخل بيانات التوصيل وسنتواصل معك لتأكيد الطلب.|No account needed. Enter your delivery details and we will contact you to confirm your order.
عنوان محفوظ|Saved address
اختر عنوانًا أو أدخل عنوانًا جديدًا|Choose an address or enter a new one
عنوان جديد|New address
بيانات التواصل والتوصيل|Contact and delivery details
الحقول بعلامة النجمة مطلوبة لضمان وصول الطلب دون تأخير.|Fields marked with an asterisk are required for smooth delivery.
طريقة الشحن|Shipping method
الوصول المتوقع خلال |Estimated delivery in 
أيام عمل.|business days.
الدفع|Payment
الدفع عند الاستلام. يتم تأكيد الطلب هاتفيًا قبل الشحن ولن نطلب منك أي بيانات بنكية.|Cash on delivery. We will call to confirm before shipping and will never ask for bank details.
طلبك|Your order
قطعة|item
تأكيد الطلب|Place order
بإتمام الطلب، أنت توافق على|By placing your order, you agree to our
شروط البيع|Terms of sale
سياسة الاسترجاع|Returns policy
تم استلام طلبك|Order received
طلبك وصلنا.|We have your order.
شكرًا|Thank you,
سنراجع التفاصيل ونتواصل معك لتأكيد الشحن.|We will review the details and contact you to confirm shipping.
رقم الطلب|Order number
احتفظ برقم الطلب ورقم هاتفك لتتمكن من متابعة الحالة في أي وقت.|Keep your order number and phone number to track your order anytime.
تتبع الطلب|Track order
العودة للمتجر|Back to shop
إغلاق السلة|Close bag
سلة التسوق|Shopping bag
تقليل الكمية|Decrease quantity
زيادة الكمية|Increase quantity
الكمية|Quantity
السلة فارغة.|Your bag is empty.
اكتشف أحدث قطع|Explore the latest MEMO pieces.
المجموع الفرعي|Subtotal
الشحن القياسي|Standard shipping
الإجمالي المتوقع|Estimated total
عرض السلة|View bag
إتمام الطلب|Checkout
فتح أو إغلاق الأقسام الفرعية|Expand or collapse subcategories
عرض كل |View all 
المتجر|Shop
كل القطع|All pieces
المجموعات|Collections
الجديد|New arrivals
المساعدة|Help
تتبع طلبك|Track your order
الاستبدال والاسترجاع|Exchanges and returns
دليل المقاسات|Size guide
تواصل معنا|Contact us
السياسات|Policies
الخصوصية|Privacy
الشروط|Terms
عن MEMO|About MEMO
الدفع عند الاستلام|Cash on delivery
الرئيسية|Home
من نحن|About us
فتح القائمة|Open menu
التنقل الرئيسي|Main navigation
بحث|Search
الحساب|Account
الحقيبة|Bag
القائمة|Menu
إغلاق القائمة|Close menu
إغلاق|Close
استكشف MEMO|Explore MEMO
أقسام المتجر|Shop categories
كل المنتجات|All products
السلة|Bag
قطع يومية، بحضور غير عادي.|Everyday pieces with a distinct presence.
عرض التفاصيل|View details
نفدت مؤقتًا|Sold out
جديد|New
لا توجد قطع هنا الآن.|No pieces here right now.
جرّب إزالة بعض الفلاتر أو اكتشف الإصدار الجديد.|Try clearing some filters or explore the latest release.
عرض كل القطع|View all pieces
إغلاق البحث|Close search
عمّ تبحث؟|What are you looking for?
اسم المنتج أو الكود|Product name or code
اكتب اسم القطعة أو الكود|Enter a product name or code
اقتراحات|Suggestions
الإصدار الجديد|New collection
هذه المساحة|This area is
ليست متاحة.|unavailable.
لا تملك صلاحية الوصول إلى هذه الصفحة.|You do not have permission to view this page.
العودة للرئيسية|Back to home
الصفحة غادرت|This page has left
المجموعة.|the collection.
قد يكون الرابط تغيّر أو أن المحتوى لم يعد متاحًا.|The link may have changed or the content may no longer be available.
اكتشف المتجر|Explore the shop
لحظة، ونعيد|One moment while we
ترتيب التفاصيل.|put things in order.
حدث خطأ غير متوقع. جرّب مرة أخرى بعد قليل.|Something went wrong. Please try again shortly.
تعديل الطلب|Edit order
تعديل بيانات الطلب|Edit order details
راجع بيانات التواصل والتوصيل، ثم احفظ التعديلات. سيراجع فريق MEMO الطلب ويتواصل معك لتأكيده.|Review your contact and delivery details, then save. The MEMO team will review your order and contact you to confirm it.
راجع البيانات التالية، ثم احفظ التعديلات وارجع إلى واتساب لتأكيد الطلب.|Review the details below, save your changes, then return to WhatsApp to confirm your order.
حفظ التعديلات|Save changes
ملخص الطلب|Order summary
بعد الحفظ أرسل في واتساب|After saving, send this on WhatsApp
لا يمكن تعديل هذا الطلب الآن.|This order cannot be edited now.
حالة الطلب الحالية|Current order status
حقيبتك|Your bag
تقليل كمية|Decrease quantity of
زيادة كمية|Increase quantity of
يمكنك اختيار الشحن السريع بقيمة |Express shipping is available for 
أثناء إتمام الطلب.|at checkout.
تطبيق|Apply
الضرائب محسوبة. الاسترجاع متاح خلال |Taxes included. Returns are available within 
يومًا وفق السياسة.|days under our policy.
متابعة التسوق|Continue shopping
حقيبتك تنتظر اختيارك.|Your bag is waiting.
اكتشف قطع الإصدار الجديد واختر ما يشبه حضورك.|Explore the latest pieces and find what suits you.
فئات المجموعة|Collection categories
اكتشف قطع|Explore pieces from
الجديدة بقصّات معاصرة وخامات مختارة.|with modern cuts and selected fabrics.
مسار القسم|Category path
قصّات معاصرة وخامات مختارة. صُممت للحضور اليومي.|Modern cuts and selected fabrics, made for everyday wear.
الأقسام الفرعية|Subcategories
عرض|View
الخصومات|Sale
الفلاتر النشطة|Active filters
فلاتر المنتجات|Product filters
الأقسام|Categories
شجرة الأقسام|Category tree
اللون|Color
المقاس|Size
المتاح فقط|In stock only
إزالة الكل|Clear all
إلى|to
تصفية النتائج|Filter results
تطبيق الفلاتر|Apply filters
اكتشف مجموعات|Explore MEMO collections
والقطع المختارة لكل إصدار.|and the selected pieces in each release.
إصدارات وقطع مختارة لتكتشف ما يناسبك.|Curated releases and pieces to discover your style.
لا توجد مجموعات متاحة حاليًا.|No collections available right now.
اكتشف المجموعة|Explore collection
اكتشف الإصدار الجديد|Explore the new collection
تعرّف على MEMO|Get to know MEMO
اسحب للاستكشاف|Scroll to explore
تسوّق حسب الفئة|Shop by category
مجموعة|Collection
المجموعة الجديدة|The new collection
قطع أساسية. جودة تدوم.|Essentials made to last.
تشغيل الفيديو|Play video
شحن لكل المحافظات|Delivery across Egypt
خيارات قياسية وسريعة|Standard and express options
تفاصيل واضحة لكل قطعة|Clear details for every piece
لا نطلب بيانات بنكية|We never ask for bank details
دعم مباشر|Direct support
رسالتك تصل للداشبورد|Your message reaches our team
استرجاع واضح|Simple returns
خلال|Within
يومًا|days
اختيارات|Selections
كن أول من يعرف الإصدار القادم.|Be first to hear about the next release.
رسائل مختصرة عند الإطلاق والعروض المهمة فقط.|Only brief updates about launches and key offers.
أدخل بريدك الإلكتروني|Enter your email
اشترك الآن|Subscribe
بالاشتراك توافق على سياسة الخصوصية، ويمكنك الإلغاء في أي وقت.|By subscribing, you agree to our privacy policy. You can unsubscribe anytime.
تسوّق الإطلالات|Shop the looks
أين طلبك؟|Where is your order?
أدخل رقم الطلب ورقم الهاتف نفسه المستخدم أثناء الشراء.|Enter your order number and the phone number used at checkout.
لم نتمكن من العثور على الطلب.|We could not find that order.
راجع رقم الطلب والهاتف ثم حاول مرة أخرى.|Check the order number and phone number, then try again.
تم الاستلام|Received
تم التأكيد|Confirmed
تم الشحن|Shipped
تم التسليم|Delivered
تاريخ الطلب|Order date
التوصيل إلى|Delivering to
آخر التحديثات|Latest updates
تم استلام الطلب وسيظهر أول تحديث بعد مراجعته.|We have received your order. The first update will appear after review.
هل تحتاج مساعدة بخصوص هذا الطلب؟|Need help with this order?
عرض صورة|View image
تكبير صورة المنتج|Enlarge product image
مسار الصفحة|Breadcrumb
خصم|Sale
توصيل قياسي خلال |Standard delivery in 
أيام عمل|business days
شحن سريع|Express shipping
استرجاع خلال |Returns within 
بدون لون|No color
بدون مقاس|No size
جارٍ التحقق من المخزون.|Checking stock.
التحقق من المخزون|Check stock
إنقاص الكمية|Decrease quantity
اشترِ الآن|Buy now
محفوظة|Saved
إضافة إلى المفضلة|Add to wishlist
مشاركة المنتج|Share product
تفاصيل المنتج|Product details
القصة|Fit
بيانات الموديل|Model details
قياسات القطعة|Measurements
الخامة والعناية|Fabric and care
الشحن خلال |Shipping in 
للقطع بحالتها الأصلية.|for items in original condition.
اقرأ السياسة كاملة|Read full policy
صور|Images
إغلاق معرض الصور|Close image gallery
الصورة السابقة|Previous image
الصورة التالية|Next image
قد يعجبك أيضًا|You may also like
نتائج|Results
ابحث في|Search MEMO
ابحث عن قطعة|Find a piece
اسم القطعة، الكود، أو المجموعة|Product name, code, or collection
نتيجة مطابقة|matching results
صفحات نتائج البحث|Search result pages
الخصم|Discount
كود الخصم|Discount code
و<a|and <a
ترتيب حسب|Sort by
الأحدث|Newest
الأقل سعرًا|Price: low to high
الأعلى سعرًا|Price: high to low
الصفحات|Pages
الصفحة السابقة|Previous page
الصفحة التالية|Next page
السعر|Price
من<input|From<input
الكل|all
تسوّق الآن|Shop now
خامات مختارة|Selected fabrics
دفع عند الاستلام|Cash on delivery
البريد الإلكتروني|Email address
الشحن والاسترجاع|Shipping and returns
الاسترجاع متاح|Returns are available
الSearch|Search
View الكل|View all
Selections MEMO|MEMO favorites
Collection MEMO|MEMO collection
item</span>|items</span>
{{ order.get_status_display }}|{{ order.status_en }}
{{ event.status_label }}|{{ event.status_label_en }}
{{ order.governorate }}|{{ order.governorate_en }}
{{ address.governorate }},|{{ address.governorate_en }},
{{ item.product_name }}|{{ item.product_name_en }}
{{ item.color_name }}|{{ item.color_name_en }}
ج.م|EGP
،|,
""".strip().splitlines()
)


def main():
    root = Path(__file__).resolve().parents[1]
    for path in (root / "templates").rglob("*.html"):
        if "dashboard" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        result = source
        for arabic, english in sorted(TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
            result = result.replace(arabic, english)
        if result != source:
            path.write_text(result, encoding="utf-8", newline="")


if __name__ == "__main__":
    main()
