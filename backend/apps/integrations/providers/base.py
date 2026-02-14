from dataclasses import dataclass


@dataclass
class SendResult:
    ok: bool
    external_id: str = ""
    error: str = ""


class MessagingProvider:
    def send_sms(self, to: str, body: str, **kwargs) -> SendResult:
        raise NotImplementedError

    def send_whatsapp(self, to: str, body: str, template_name: str = "", **kwargs) -> SendResult:
        raise NotImplementedError


class EmailProvider:
    def send_email(self, to: str, subject: str, body: str, **kwargs) -> SendResult:
        raise NotImplementedError


class PaymentProvider:
    def create_intent(self, amount, currency: str, reference_type: str, reference_id, **kwargs):
        """
        Must return: (payment_url, external_id, provider_payload)
        """
        raise NotImplementedError
