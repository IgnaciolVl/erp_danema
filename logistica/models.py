from django.db import models
#Clases
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='productos')
    sku = models.CharField(max_length=50, unique=True, help_text="Código de barras")
    nombre = models.CharField(max_length=200)
    precio = models.IntegerField()
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2)
    stock_disponible = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.sku} - {self.nombre}"

class Cliente(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=255)
    comuna = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.rut})"

class Pedido(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Armado'),
        ('EMPACANDO', 'Empacando / Preparando'),
        ('DESPACHADO', 'Entregado a Chilexpress'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='pedidos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    tracking_chilexpress = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.nombre} - {self.estado}"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.IntegerField()

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} (Pedido #{self.pedido.id})"

