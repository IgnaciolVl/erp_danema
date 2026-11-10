from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import Categoria, Subcategoria, Producto, Cliente, Pedido
from .serializers import (
    CategoriaSerializer, SubcategoriaSerializer, 
    ProductoSerializer, ClienteSerializer, PedidoSerializer
)
from .chilexpress import ChilexpressAPI


class EsSuperAdminOSoloLectura(IsAuthenticated):
    """RN-02: Solo SuperAdmins pueden crear, editar o borrar categorías."""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return bool(request.user and request.user.is_superuser)


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [EsSuperAdminOSoloLectura]


class SubcategoriaViewSet(viewsets.ModelViewSet):
    queryset = Subcategoria.objects.all()
    serializer_class = SubcategoriaSerializer
    permission_classes = [EsSuperAdminOSoloLectura]


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer


class PedidoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save(operador_bodega=request.user)

        chilexpress = ChilexpressAPI()
        comuna_destino = pedido.direccion_envio.comuna.codigo_chilexpress
        
        cotizacion = {
            "mensaje": f"Pedido #{pedido.id} registrado y stock descontado.",
            "origen": "MOST",
            "destino": comuna_destino,
            "peso_caja_kg": pedido.peso_total_kg,
        }

        response_data = serializer.data
        response_data['logistica'] = cotizacion
        return Response(response_data, status=status.HTTP_201_CREATED)