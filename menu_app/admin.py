from django.contrib import admin
from .models import MenuItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu_name', 'parent', 'order', 'get_url_display')
    list_filter = ('menu_name',)
    list_editable = ('order',)
    search_fields = ('name', 'menu_name', 'named_url', 'explicit_url')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'menu_name', 'order')
        }),
        ('Ссылка', {
            'fields': ('named_url', 'explicit_url'),
            'description': 'Укажите named URL (из urls.py) ИЛИ explicit URL'
        }),
        ('Структура', {
            'fields': ('parent',),
            'description': 'Выберите родительский пункт для создания вложенности'
        }),
    )

    def get_url_display(self, obj):
        url = obj.get_url()
        if url == '#':
            return '—'
        return url

    get_url_display.short_description = 'URL'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')
