from django.contrib import admin
from .models import (
    Region, Comuna, Categoria, Subcategoria, 
    Producto, Cliente, DireccionEnvio, Pedido, DetallePedido
)

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'codigo_iso')

@admin.register(Comuna)
class ComunaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'region', 'codigo_chilexpress')
    list_filter = ('region',)
    search_fields = ('nombre', 'codigo_chilexpress')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'prefijo_sku')

@admin.register(Subcategoria)
class SubcategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'prefijo_sku', 'categoria')
    list_filter = ('categoria',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'nombre', 'subcategoria', 'precio_venta', 'stock_actual', 'activo')
    list_filter = ('subcategoria__categoria', 'subcategoria', 'activo')
    search_fields = ('sku', 'nombre', 'codigo_barras_ean')
    readonly_fields = ('fecha_creacion',)

class DireccionEnvioInline(admin.TabularInline):
    model = DireccionEnvio
    extra = 1

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombres', 'apellidos', 'telefono', 'tipo_documento_preferido')
    search_fields = ('rut', 'nombres', 'apellidos')
    inlines = [DireccionEnvioInline]

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'canal_venta', 'estado', 'total_final', 'fecha_creacion')
    list_filter = ('estado', 'canal_venta', 'tipo_documento')
    inlines = [DetallePedidoInline]