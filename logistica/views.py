from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from .models import Producto, Pedido
from .serializers import ProductoSerializer, PedidoSerializer
from .chilexpress import ChilexpressAPI

class ProductoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

class PedidoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer

    def create(self, request, *args, **kwargs):
        # 1. El serializador recibe el JSON y descuenta el stock de la base de datos
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()

        # 2. Nos comunicamos con Chilexpress
        chilexpress = ChilexpressAPI()
        
        # Como aún no enviamos direcciones reales, haremos un cotizador de prueba
        # usando el peso total que acabas de programar en models.py
        cotizacion = {
            "mensaje": f"Pedido #{pedido.id} creado con éxito y stock descontado.",
            "peso_caja_kg": pedido.peso_total_kg,
            "estado_chilexpress": "Pendiente de integración de origen/destino"
        }

        # 3. Retornamos la respuesta al cliente
        # Aquí sumamos la información del pedido (del serializador) más la cotización
        response_data = serializer.data
        response_data['logistica'] = cotizacion

        return Response(response_data, status=status.HTTP_201_CREATED)