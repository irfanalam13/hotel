from django.db import transaction
from django.utils import timezone

from .models import PaymentIntent, IntegrationKind
from .providers.registry import get_payment_provider
from .services import get_config


@transaction.atomic
def create_payment_intent(*, tenant_id, amount, currency="NPR", reference_type="reservation", reference_id=None):
    cfg = get_config(tenant_id, IntegrationKind.PAYMENT)
    provider = (cfg.provider if cfg else "mock")

    intent = PaymentIntent.objects.create(
        tenant_id=tenant_id,
        provider=provider,
        amount=amount,
        currency=currency,
        reference_type=reference_type,
        reference_id=reference_id,
        status=PaymentIntent.Status.CREATED,
    )

    prov = get_payment_provider(provider)
    payment_url, external_id, payload = prov.create_intent(amount, currency, reference_type, reference_id)

    intent.payment_url = payment_url
    intent.external_id = external_id
    intent.provider_payload = payload or {}
    intent.status = PaymentIntent.Status.REDIRECTED
    intent.save(update_fields=["payment_url", "external_id", "provider_payload", "status"])
    return intent


@transaction.atomic
def mark_intent_paid(*, intent: PaymentIntent, provider_payload=None):
    intent.status = PaymentIntent.Status.PAID
    intent.paid_at = timezone.now()
    if provider_payload:
        intent.provider_payload = {**(intent.provider_payload or {}), **provider_payload}
    intent.save(update_fields=["status", "paid_at", "provider_payload"])
    return intent
