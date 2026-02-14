from django.utils import timezone
from .models import SupportTicket


def mark_first_response(ticket: SupportTicket) -> None:
    if ticket.first_response_at is None:
        ticket.first_response_at = timezone.now()
        ticket.save(update_fields=["first_response_at"])


def close_ticket(ticket: SupportTicket) -> None:
    if ticket.resolved_at is None:
        ticket.resolved_at = timezone.now()
    ticket.status = "closed"
    ticket.save(update_fields=["status", "resolved_at"])
