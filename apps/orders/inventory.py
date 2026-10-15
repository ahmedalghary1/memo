import logging

from django.db.models import F

from apps.catalog.models import InventoryMovement, ProductVariant
from apps.orders.models import Coupon

logger = logging.getLogger(__name__)


def restore_cancelled_order_stock(order):
    """Call after locking an order and only on its first transition to cancelled."""
    for item in order.items.all():
        variant = ProductVariant.objects.filter(pk=item.variant_id).first() if item.variant_id else ProductVariant.objects.filter(sku=item.variant_sku).first()
        if variant is None:
            logger.error("Cannot restore stock for order %s, SKU %s", order.order_number, item.variant_sku)
            continue
        ProductVariant.objects.filter(pk=variant.pk).update(stock_quantity=F("stock_quantity") + item.quantity)
        InventoryMovement.objects.create(
            variant=variant, movement_type="return", quantity=item.quantity,
            reference=order.order_number, note="إعادة المخزون بعد إلغاء الطلب",
        )
    if order.coupon_id:
        Coupon.objects.filter(pk=order.coupon_id, uses__gt=0).update(uses=F("uses") - 1)
