from rest_framework import serializers
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import Categoria, Producto, Cliente, Pedido, DetallePedido

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion']

class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    class Meta:
        model = Producto
        fields = ['id', 'categoria', 'sku', 'nombre', 'precio', 'peso_kg', 'stock_disponible', 'categoria_nombre']

# 1. CREAMOS EL SERIALIZADOR PARA LOS PRODUCTOS DEL CARRITO
class DetallePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePedido
        fields = ['producto', 'cantidad', 'precio_unitario']

class PedidoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    
    # 2. LE DECIMOS AL PEDIDO QUE ESPERE RECIBIR UNA LISTA DE DETALLES
    detalles = DetallePedidoSerializer(many=True)

    class Meta:
        model = Pedido
        # 3. AGREGAMOS 'detalles' A LOS FIELDS (esto era lo que intuías)
        fields = ['id', 'cliente', 'fecha_creacion', 'estado', 'tracking_chilexpress', 'cliente_nombre', 'detalles']

    # 4. EL MOTOR TRANSACCIONAL: La matemática que resta el stock
    @transaction.atomic
    def create(self, validated_data):
        # Extraemos la lista de productos del JSON
        detalles_data = validated_data.pop('detalles')
        
        # Creamos la cabecera del Pedido
        pedido = Pedido.objects.create(**validated_data)
        
        # Iteramos por cada producto que el cliente quiere comprar
        for detalle_data in detalles_data:
            producto = detalle_data['producto']
            cantidad_comprada = detalle_data['cantidad']
            
            # Verificamos si hay stock suficiente
            if producto.stock_disponible < cantidad_comprada:
                raise ValidationError({
                    "error": f"No hay stock suficiente de {producto.nombre}. Stock actual: {producto.stock_disponible}"
                })
            
            # RESTAMOS EL STOCK Y GUARDAMOS
            producto.stock_disponible -= cantidad_comprada
            producto.save()
            
            # Guardamos el detalle asociándolo a este pedido
            DetallePedido.objects.create(pedido=pedido, **detalle_data)
            
        return pedido