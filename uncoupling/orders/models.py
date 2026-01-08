from django.db import models
from my_auth.models import MeliUser


class Order(models.Model):
    STATUS_CHOICES = [
        ('paid', 'Pagada'),
        ('confirmed', 'Confirmada'),
        ('payment_required', 'Pago requerido'),
        ('payment_in_process', 'Pago en proceso'),
        ('cancelled', 'Cancelada'),
        ('invalid', 'Inválida'),
    ]

    # Primary fields
    id = models.BigIntegerField(primary_key=True)
    meli_user = models.ForeignKey(MeliUser, on_delete=models.CASCADE, related_name='orders')

    # Order basic info
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    date_created = models.DateTimeField()
    date_closed = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField()

    # Buyer info
    buyer_id = models.BigIntegerField()
    buyer_nickname = models.CharField(max_length=255, null=True, blank=True)
    buyer_email = models.EmailField(null=True, blank=True)
    buyer_phone = models.CharField(max_length=50, null=True, blank=True)
    buyer_first_name = models.CharField(max_length=255, null=True, blank=True)
    buyer_last_name = models.CharField(max_length=255, null=True, blank=True)

    # Totals
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency_id = models.CharField(max_length=10)

    # Shipping info
    shipping_id = models.BigIntegerField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['meli_user', '-date_created']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'Order {self.id} - {self.status} - ${self.total_amount}'

    def get_total_items(self):
        """Calculate total number of items in order"""
        return sum(item.quantity for item in self.order_items.all())


class OrderItem(models.Model):
    """Item in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    item_id = models.CharField(max_length=50)
    title = models.TextField()
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency_id = models.CharField(max_length=10)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f'{self.title} x{self.quantity}'


class Payment(models.Model):
    """Payment for an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_id = models.BigIntegerField()
    transaction_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency_id = models.CharField(max_length=10)
    status = models.CharField(max_length=50)
    payment_type = models.CharField(max_length=50, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f'Payment {self.payment_id} - {self.status} - ${self.transaction_amount}'
