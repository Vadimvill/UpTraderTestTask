from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import MenuItem


@receiver([post_save, post_delete], sender=MenuItem)
def clear_menu_cache(sender, **kwargs):
    instance = kwargs['instance']
    cache_key = f"menu_items_{instance.menu_name}"
    cache.delete(cache_key)
