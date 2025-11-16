import uuid

from django.db import models
from django.urls import reverse, NoReverseMatch
from django.utils.translation import gettext_lazy as _


class MenuItem(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    name = models.CharField(
        _('name'),
        max_length=100,
    )
    named_url = models.CharField(
        _('named URL'),
        max_length=100,
        blank=True,
    )
    explicit_url = models.CharField(
        _('explicit URL'),
        max_length=200,
        blank=True,
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('parent menu item'),
    )
    menu_name = models.CharField(
        _('menu name'),
        max_length=50,
    )
    order = models.IntegerField(
        _('order'),
        default=0,
    )

    class Meta:
        verbose_name = _('menu item')
        verbose_name_plural = _('menu items')
        ordering = ['menu_name', 'order', 'name']

    def __str__(self):
        return f"{self.menu_name}: {self.name}"

    def get_url(self):
        if self.named_url:
            try:
                return reverse(self.named_url)
            except NoReverseMatch:
                return self.named_url
        elif self.explicit_url:
            return self.explicit_url
        return '#'

    @property
    def has_children(self):
        return self.children.exists()
