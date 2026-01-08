from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        import orders.signals  # noqa: F401
        from orders.containers import order_container

        order_container.wire(modules=['orders.views', 'orders.signals'])
