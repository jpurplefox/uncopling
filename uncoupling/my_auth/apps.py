from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_auth'

    def ready(self):
        from my_auth.containers import auth_container

        auth_container.wire(modules=['my_auth.views'])
