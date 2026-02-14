from celery import shared_task
from .models import OutboundMessage
from .services import send_outbound_message


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_message_task(self, message_id: str):
    msg = OutboundMessage.objects.get(id=message_id)
    msg = send_outbound_message(msg)
    if msg.status == OutboundMessage.Status.FAILED:
        raise self.retry(exc=Exception(msg.error))
    return {"ok": True, "status": msg.status, "external_id": msg.external_id}
