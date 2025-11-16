from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import MenuItem


@receiver([post_save, post_delete], sender=MenuItem)
  try:
        instance = kwargs.get('instance')
        if not instance or not hasattr(instance, 'menu_name'):
            return
        cache_key = f"menu_items_{instance.menu_name}"
        cache.delete(cache_key)
        
    except Exception as e:
        ...
