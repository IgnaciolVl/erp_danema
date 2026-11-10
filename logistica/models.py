from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# 1. MÓDULO GEOGRÁFICO (PARAMÉTRICO PARA CHILEXPRESS)

class Region(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo_iso = models.CharField(max_length=10, unique=True, help_text="Ej: CL-LI para O'Higgins, CL-RM para Metropolitana")

    class Meta:
        verbose_name = "Región"
        verbose_name_plural = "Regiones"
        ordering = ['id']

    def __str__(self):
        return self.nombre


class Comuna(models.Model):
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='comunas')
    nombre = models.CharField(max_length=100)
    codigo_chilexpress = models.CharField(
        max_length=20, 
        unique=True, 
        help_text="Código oficial de cobertura Chilexpress (Ej: MOST para Mostazal, STGO para Santiago)"
    )

    class Meta:
        verbose_name = "Comuna"
        verbose_name_plural = "Comunas"
        unique_together = ('region', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.region.codigo_iso})"


# 2. CATÁLOGO, BODEGA Y GENERADOR AUTOMÁTICO DE SKU

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    prefijo_sku = models.CharField(
        max_length=3, 
        unique=True, 
        help_text="3 letras para el SKU automático. Ej: HOG (Hogar), PAP (Papelería)"
    )
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def save(self, *args, **kwargs):
        self.prefijo_sku = self.prefijo_sku.upper().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} [{self.prefijo_sku}]"


class Subcategoria(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='subcategorias')
    nombre = models.CharField(max_length=100)
    prefijo_sku = models.CharField(
        max_length=3, 
        help_text="3 letras para la subcategoría. Ej: VEL (Velas), CUA (Cuadernos)"
    )

    class Meta:
        verbose_name = "Subcategoría"
        verbose_name_plural = "Subcategorías"
        unique_together = ('categoria', 'nombre')

    def save(self, *args, **kwargs):
        self.prefijo_sku = self.prefijo_sku.upper().strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.categoria.nombre} > {self.nombre} [{self.prefijo_sku}]"


class Producto(models.Model):
    subcategoria = models.ForeignKey(Subcategoria, on_delete=models.PROTECT, related_name='productos')
    sku = models.CharField(
        max_length=30, 
        unique=True, 
        blank=True, 
        help_text="Se genera automáticamente si se deja en blanco (Ej: HOG-VEL-0001)"
    )
    codigo_barras_ean = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True, 
        help_text="Código de barras del fabricante (opcional, si el producto ya trae uno impreso)"
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    
    # Precios y Control de Inventario
    precio_venta = models.PositiveIntegerField(help_text="Precio final con IVA incluido (CLP)")
    costo_unitario = models.PositiveIntegerField(default=0, help_text="Costo de compra neto o bruto para calcular margen")
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo_alerta = models.PositiveIntegerField(default=5, help_text="Alerta cuando quedan pocas unidades en bodega")
    
    # Dimensiones Físicas para Cotizador de Chilexpress
    peso_kg = models.FloatField(help_text="Peso en kilogramos (Ej: 0.25 para 250 gramos)")
    largo_cm = models.FloatField(default=10.0, help_text="Largo en cm")
    ancho_cm = models.FloatField(default=10.0, help_text="Ancho en cm")
    alto_cm = models.FloatField(default=10.0, help_text="Alto en cm")
    
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def save(self, *args, **kwargs):
        # MOTOR GENERADOR DE SKU AUTOMÁTICO 
        if not self.sku:
            prefijo_cat = self.subcategoria.categoria.prefijo_sku
            prefijo_sub = self.subcategoria.prefijo_sku
            base_sku = f"{prefijo_cat}-{prefijo_sub}"
            
            # Contamos cuántos productos existen en esta subcategoría para el correlativo
            ultimo_producto = Producto.objects.filter(sku__startswith=base_sku).order_by('id').last()
            if ultimo_producto and ultimo_producto.sku:
                try:
                    ultimo_numero = int(ultimo_producto.sku.split('-')[-1])
                    nuevo_numero = ultimo_numero + 1
                except ValueError:
                    nuevo_numero = Producto.objects.filter(subcategoria=self.subcategoria).count() + 1
            else:
                nuevo_numero = 1
                
            self.sku = f"{base_sku}-{nuevo_numero:04d}"
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.sku}] {self.nombre} (Stock: {self.stock_actual})"


# 3. MÓDULO DE CLIENTES Y DIRECCIONES NORMALIZADAS

class Cliente(models.Model):
    TIPO_DOC_CHOICES = [
        ('BOLETA', 'Boleta Electrónica (Persona Natural)'),
        ('FACTURA', 'Factura Electrónica (Empresa / Colegio)'),
    ]

    # Enlace 1 a 1 opcional con Login de Django 
    usuario = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='perfil_cliente',
        help_text="Cuenta de usuario para login en la web de Danema"
    )
    rut = models.CharField(max_length=12, unique=True, help_text="Formato: 12345678-9")
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, help_text="Ej: +56912345678 (Requerido por Chilexpress)")
    
    # Soporte para Facturación
    tipo_documento_preferido = models.CharField(max_length=10, choices=TIPO_DOC_CHOICES, default='BOLETA')
    razon_social = models.CharField(max_length=200, blank=True, null=True, help_text="Solo si pide Factura")
    giro_comercial = models.CharField(max_length=200, blank=True, null=True, help_text="Solo si pide Factura")
    
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def clean(self):
        # Validación de regla de negocio para Facturas
        if self.tipo_documento_preferido == 'FACTURA' and (not self.razon_social or not self.giro_comercial):
            raise ValidationError("Para emitir Factura es obligatorio indicar Razón Social y Giro Comercial.")

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.rut})"


class DireccionEnvio(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='direcciones')
    comuna = models.ForeignKey(Comuna, on_delete=models.PROTECT, related_name='direcciones_clientes')
    alias = models.CharField(max_length=50, default="Casa", help_text="Ej: Casa, Oficina, Bodega Recepción")
    calle = models.CharField(max_length=150)
    numero = models.CharField(max_length=20)
    depto_oficina = models.CharField(max_length=50, blank=True, null=True, help_text="Opcional: Depto, Block, Oficina")
    referencia = models.CharField(max_length=255, blank=True, null=True, help_text="Indicaciones para el repartidor")
    es_principal = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Dirección de Envío"
        verbose_name_plural = "Direcciones de Envío"

    def save(self, *args, **kwargs):
        # Si esta dirección se marca como principal, desmarcamos las demás de este cliente
        if self.es_principal:
            DireccionEnvio.objects.filter(cliente=self.cliente, es_principal=True).update(es_principal=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.alias}: {self.calle} #{self.numero}, {self.comuna.nombre}"



# 4. MÓDULO TRANSACCIONAL DE PEDIDOS Y DESPACHOS

class Pedido(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Armado'),
        ('EMPACANDO', 'Empacando en Bodega'),
        ('LISTO_DESPACHO', 'Etiquetado / Listo para Chilexpress'),
        ('DESPACHADO', 'Entregado a Chilexpress'),
        ('ENTREGADO', 'Entregado al Cliente Final'),
        ('CANCELADO', 'Cancelado / Stock Devuelto'),
    ]

    CANALES = [
        ('WEB_DANEMA', 'Sitio Web / App Danema'),
        ('MERCADOLIBRE', 'MercadoLibre'),
        ('VENTA_DIRECTA', 'Venta Directa / Manual'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='pedidos')
    direccion_envio = models.ForeignKey(
        DireccionEnvio, 
        on_delete=models.PROTECT, 
        related_name='pedidos_despachados',
        help_text="Dirección exacta a la que se enviará esta caja"
    )
    operador_bodega = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='pedidos_preparados',
        help_text="Trabajador que armó y escaneó la caja en bodega"
    )
    
    canal_venta = models.CharField(max_length=20, choices=CANALES, default='WEB_DANEMA')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    tipo_documento = models.CharField(max_length=10, choices=Cliente.TIPO_DOC_CHOICES, default='BOLETA')
    
    costo_envio = models.PositiveIntegerField(default=0, help_text="Valor calculado por API Chilexpress (CLP)")
    tracking_chilexpress = models.CharField(max_length=100, blank=True, null=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.nombres} {self.cliente.apellidos} [{self.estado}]"

    @property
    def peso_total_kg(self):
        total = sum(detalle.producto.peso_kg * detalle.cantidad for detalle in self.detalles.all())
        return round(total, 2)

    @property
    def subtotal_productos(self):
        return sum(detalle.precio_unitario * detalle.cantidad for detalle in self.detalles.all())

    @property
    def total_final(self):
        return self.subtotal_productos + self.costo_envio


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.PositiveIntegerField(help_text="Precio congelado al momento de la venta")

    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedidos"

    def __str__(self):
        return f"{self.cantidad}x [{self.producto.sku}] {self.producto.nombre} (Pedido #{self.pedido.id})"