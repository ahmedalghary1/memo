from abc import ABC, abstractmethod
class PaymentGateway(ABC):
    @abstractmethod
    def create_payment(self, order): ...
class CashOnDeliveryGateway(PaymentGateway):
    def create_payment(self, order): return {"status": "pending", "reference": order.order_number}
