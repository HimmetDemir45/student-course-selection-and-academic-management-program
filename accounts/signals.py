from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User
from accounts.services.profile_provisioning import provision_role_profiles


def _sync_role_group(instance: User) -> None:
    role = (instance.role or User.Role.STUDENT).strip()
    if not role:
        return
    group, _ = Group.objects.get_or_create(name=role)
    instance.groups.set([group])


@receiver(post_save, sender=User)
def on_user_post_save(sender, instance, **kwargs):
    _sync_role_group(instance)
    provision_role_profiles(instance)
