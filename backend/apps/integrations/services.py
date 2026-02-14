from django.utils import timezone
from django.db import transaction

from .models import IntegrationConfig, MessageTemplate, OutboundMessage, IntegrationKind
from .providers.registry import get_messaging_provider, get_email_provider
from .utils import render_template


def get_config(tenant_id, kind: str) -> IntegrationConfig | None:
    return IntegrationConfig.objects.filter(tenant_id=tenant_id, kind=kind, is_enabled=True).first()


@transaction.atomic
def queue_message(*, tenant_id, kind: str, to: str, subject: str = "", body: str = "", created_by=None, metadata=None):
    cfg = get_config(tenant_id, kind)
    provider = (cfg.provider if cfg else "mock")
    msg = OutboundMessage.objects.create(
        tenant_id=tenant_id,
        kind=kind,
        provider=provider,
        to=to,
        subject=subject or "",
        body=body or "",
        metadata=metadata or {},
        created_by=created_by,
        status=OutboundMessage.Status.QUEUED,
    )
    return msg


def render_from_template(*, tenant_id, kind: str, code: str, ctx: dict):
    tpl = MessageTemplate.objects.filter(tenant_id=tenant_id, kind=kind, code=code, is_active=True).first()
    if not tpl:
        return "", "", ""
    subject = render_template(tpl.subject, ctx)
    body = render_template(tpl.body, ctx)
    return tpl, subject, body


def send_outbound_message(msg: OutboundMessage):
    # pick provider based on msg.provider (in registry currently mock)
    try:
        if msg.kind in (IntegrationKind.SMS, IntegrationKind.WHATSAPP):
            prov = get_messaging_provider(msg.provider)
            if msg.kind == IntegrationKind.SMS:
                res = prov.send_sms(msg.to, msg.body)
            else:
                res = prov.send_whatsapp(msg.to, msg.body, template_name=msg.metadata.get("wa_template_name", ""))
        elif msg.kind == IntegrationKind.EMAIL:
            prov = get_email_provider(msg.provider)
            res = prov.send_email(msg.to, msg.subject, msg.body)
        else:
            raise ValueError("Unsupported kind for outbound send")

        if res.ok:
            msg.status = OutboundMessage.Status.SENT
            msg.external_id = res.external_id
            msg.sent_at = timezone.now()
            msg.error = ""
        else:
            msg.status = OutboundMessage.Status.FAILED
            msg.error = res.error or "Unknown error"
        msg.save(update_fields=["status", "external_id", "sent_at", "error"])
        return msg

    except Exception as e:
        msg.status = OutboundMessage.Status.FAILED
        msg.error = str(e)
        msg.save(update_fields=["status", "error"])
        return msg
