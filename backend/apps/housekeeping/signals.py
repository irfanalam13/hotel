from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.rooms.models import RoomStatus
from .models import CleaningTask, HKTaskPriority, HKTaskStatus

# CHANGE THIS MODEL IMPORT TO MATCH YOUR PROJECT:
from apps.reservations.models import Stay  # must have: tenant, room, status/checked_out flag


@receiver(post_save, sender=Stay)
def create_cleaning_task_after_checkout(sender, instance: Stay, created, **kwargs):
    """
    Real-life rule:
    - When checkout happens => room becomes VACANT_DIRTY
    - Create CleaningTask (PENDING) with due time (e.g., 60-120 minutes)
    """
    if instance.status != "checked_out":
        return

    room = instance.room
    if room.status != RoomStatus.OUT_OF_ORDER:
        room.status = RoomStatus.VACANT_DIRTY
        room.save(update_fields=["status"])

    # avoid duplicates
    exists = CleaningTask.objects.filter(
        tenant=instance.tenant,
        room=room,
        stay_id=str(instance.id),
    ).exists()
    if exists:
        return

    due_at = timezone.now() + timezone.timedelta(minutes=90)

    CleaningTask.objects.create(
        tenant=instance.tenant,
        room=room,
        stay_id=str(instance.id),
        status=HKTaskStatus.PENDING,
        priority=HKTaskPriority.HIGH,
        due_at=due_at,
        notes="Auto-created from checkout.",
    )
