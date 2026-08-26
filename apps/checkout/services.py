from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    @abstractmethod
    def create_payment(self, order):
        """Create a payment attempt and return its normalized state."""
        raise NotImplementedError("Payment gateways must implement create_payment().")


class CashOnDeliveryGateway(PaymentGateway):
    def create_payment(self, order):
        return {
            "status": "pending",
            "reference": order.order_number,
            "provider": "cash_on_delivery",
            "amount": str(order.grand_total),
        }
