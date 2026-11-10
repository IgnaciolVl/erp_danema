from rest_framework import serializers
from django.db import transaction
from .models import (
    Region, Comuna, Categoria, Subcategoria, 
    Producto, Cliente, DireccionEnvio, Pedido, DetallePedido
)

class ComunaSerializer(serializers.ModelSerializer):
    region_nombre = serializers.CharField(source='region.nombre', read_only=True)

    class Meta:
        model = Comuna
        fields = ['id', 'nombre', 'codigo_chilexpress', 'region', 'region_nombre']


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class SubcategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategoria
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    subcategoria_nombre = serializers.CharField(source='subcategoria.nombre', read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'sku', 'codigo_barras_ean', 'nombre', 'descripcion',
            'subcategoria', 'subcategoria_nombre', 'precio_venta', 
            'stock_actual', 'peso_kg', 'largo_cm', 'ancho_cm', 'alto_cm', 'activo'
        ]
        read_only_fields = ['sku']


class DireccionEnvioSerializer(serializers.ModelSerializer):
    comuna_nombre = serializers.CharField(source='comuna.nombre', read_only=True)

    class Meta:
        model = DireccionEnvio
        fields = ['id', 'alias', 'calle', 'numero', 'depto_oficina', 'referencia', 'comuna', 'comuna_nombre', 'es_principal']


class ClienteSerializer(serializers.ModelSerializer):
    direcciones = DireccionEnvioSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = [
            'id', 'rut', 'nombres', 'apellidos', 'telefono', 
            'tipo_documento_preferido', 'razon_social', 'giro_comercial', 'direcciones'
        ]

    def to_representation(self, instance):
        """
        RN-05: Si el usuario autenticado NO es SuperAdmin ni el dueño de la cuenta,
        enmascaramos los datos sensibles en pantalla.
        """
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        es_admin = request and request.user and request.user.is_superuser
        es_dueno = request and request.user and (instance.usuario == request.user)

        if not (es_admin or es_dueno):
            data['rut'] = "***.***.***-*"
            data['telefono'] = "+569********"
            for dir_envio in data.get('direcciones', []):
                dir_envio['calle'] = "******** (Protegido por Rol)"
                dir_envio['numero'] = "***"
        return data


class DetallePedidoSerializer(serializers.ModelSerializer):
    producto_sku = serializers.CharField(source='producto.sku', read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = DetallePedido
        fields = ['producto', 'producto_sku', 'producto_nombre', 'cantidad', 'precio_unitario']


class PedidoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombres', read_only=True)
    peso_total_kg = serializers.FloatField(read_only=True)
    subtotal_productos = serializers.IntegerField(read_only=True)
    total_final = serializers.IntegerField(read_only=True)
    detalles = DetallePedidoSerializer(many=True)

    class Meta:
        model = Pedido
        fields = [
            'id', 'cliente', 'cliente_nombre', 'direccion_envio', 'canal_venta',
            'estado', 'tipo_documento', 'costo_envio', 'tracking_chilexpress',
            'peso_total_kg', 'subtotal_productos', 'total_final', 'fecha_creacion', 'detalles'
        ]

    @transaction.atomic
    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        pedido = Pedido.objects.create(**validated_data)

        for detalle in detalles_data:
            producto = Producto.objects.select_for_update().get(id=detalle['producto'].id)
            cantidad_pedida = detalle['cantidad']

            if producto.stock_actual < cantidad_pedida:
                raise serializers.ValidationError(
                    f"Stock insuficiente para '{producto.nombre}' (SKU: {producto.sku}). "
                    f"Disponible: {producto.stock_actual}, Solicitado: {cantidad_pedida}."
                )

            producto.stock_actual -= cantidad_pedida
            producto.save()

            DetallePedido.objects.create(pedido=pedido, **detalle)

        return pedido