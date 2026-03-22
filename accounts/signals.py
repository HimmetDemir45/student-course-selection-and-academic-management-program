from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User


@receiver(post_save, sender=User)
def sync_role_group(sender, instance, **kwargs):
    role = (instance.role or User.Role.STUDENT).strip()
    if not role:
        return
    group, _ = Group.objects.get_or_create(name=role)
    instance.groups.set([group])
