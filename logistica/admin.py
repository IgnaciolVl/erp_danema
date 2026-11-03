from django.contrib import admin
from .models import Categoria, Producto, Cliente, Pedido, DetallePedido

admin.site.site_header = "ERP Danema - Administración"
admin.site.site_title = "Panel ERP"
admin.site.index_title = "Centro de Control de Operaciones"

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'sku', 'nombre', 'categoria', 'precio', 'peso_kg', 'stock_disponible')
    list_filter = ('categoria',)
    search_fields = ('sku', 'nombre')
    ordering = ('-id',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'rut', 'nombre', 'comuna', 'telefono', 'email')
    search_fields = ('rut', 'nombre', 'email', 'comuna')

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'estado', 'fecha_creacion', 'tracking_chilexpress')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('cliente__nombre', 'cliente__rut', 'tracking_chilexpress')
    inlines = [DetallePedidoInline]