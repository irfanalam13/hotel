from .base import MessagingProvider, EmailProvider, PaymentProvider, SendResult
import uuid


class MockMessaging(MessagingProvider):
    def send_sms(self, to: str, body: str, **kwargs) -> SendResult:
        return SendResult(ok=True, external_id=f"mock_sms_{uuid.uuid4()}")

    def send_whatsapp(self, to: str, body: str, template_name: str = "", **kwargs) -> SendResult:
        return SendResult(ok=True, external_id=f"mock_wa_{uuid.uuid4()}")


class MockEmail(EmailProvider):
    def send_email(self, to: str, subject: str, body: str, **kwargs) -> SendResult:
        return SendResult(ok=True, external_id=f"mock_email_{uuid.uuid4()}")


class MockPayment(PaymentProvider):
    def create_intent(self, amount, currency: str, reference_type: str, reference_id, **kwargs):
        external_id = f"mock_pay_{uuid.uuid4()}"
        payment_url = f"https://example.com/mock-pay/{external_id}"
        return payment_url, external_id, {"mock": True}
