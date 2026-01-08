from django.contrib import admin
from orders.models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'meli_user', 'status', 'total_amount', 'date_created')
    list_filter = ('status', 'date_created')
    search_fields = ('id', 'buyer_nickname', 'buyer_email')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date_created'
    inlines = [OrderItemInline, PaymentInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'title', 'quantity', 'unit_price')
    list_filter = ('currency_id',)
    search_fields = ('title', 'item_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'payment_id', 'status', 'transaction_amount')
    list_filter = ('status', 'payment_type')
    search_fields = ('payment_id',)
    readonly_fields = ('created_at', 'updated_at')
