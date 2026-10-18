from django.contrib import admin
from .models import Categoria, Producto, Cliente, Pedido, DetallePedido

# Modelos  
admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(Cliente)
admin.site.register(Pedido)
admin.site.register(DetallePedido) 