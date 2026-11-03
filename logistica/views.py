from rest_framework import viewsets, mixins
from .models import Producto, Pedido    
from .serializers import ProductoSerializer, PedidoSerializer   

class ProductoViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Producto.objects.filter(stock_disponible__gt=0) # Solo mostramos productos con stock mayor a 0
    serializer_class = ProductoSerializer

class PedidoViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Pedido.objects.all().order_by('-fecha_creacion')  # Ordenamos los pedidos por fecha de creación, del más reciente al más antiguo
    serializer_class = PedidoSerializer