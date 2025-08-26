from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from .models import User, Whitelist
from .tasks import sync_access_from_whitelist


@receiver(m2m_changed, sender=Whitelist.courses.through)
def on_whitelist_courses_change(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        sync_access_from_whitelist.delay(str(instance.phone_number))


@receiver(post_delete, sender=Whitelist)
def on_whitelist_entry_delete(sender, instance, **kwargs):
    sync_access_from_whitelist.delay(str(instance.phone_number))


@receiver(post_save, sender=User)
def on_user_create_or_update(sender, instance, created, **kwargs):
    if created and instance.phone_number:
        sync_access_from_whitelist.delay(str(instance.phone_number))
