from django.apps import AppConfig


class MenuConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "menu_app"

    def ready(self):
        import menu_app.signals
