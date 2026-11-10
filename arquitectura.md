# Documentación de Arquitectura y Especificación de Requerimientos (SRS)
**Proyecto:** ERP & E-Commerce Core — Danema SpA  
**Ubicación Operativa:** Mostazal, Región de O'Higgins, Chile  
**Versión:** 1.0  

---

## 1. Propósito y Alcance
Sistema integral de planificación de recursos empresariales (ERP) y comercio electrónico híbrido para **Danema SpA**. El sistema centraliza el control de stock en bodega en tiempo real, automatiza la generación de códigos SKU para etiquetado físico/lectura por escáner, cotiza despachos vía API de Chilexpress y gestiona el acceso mediante roles granulares y cifrado de datos sensibles.

---

## 2. Perfiles de Usuario y Control de Acceso (RBAC)
* **ROL-01 (SuperAdmin / Gerencia):** Control total del ERP. Único rol autorizado para crear/editar/eliminar categorías, subcategorías, visualizar datos personales sensibles de clientes (RUT, teléfono, dirección) y acceder a métricas financieras.
* **ROL-02 (Operador de Bodega):** Acceso restringido a módulos operativos. Autorizado únicamente para recepcionar mercadería, imprimir etiquetas de código de barras (SKU), consultar stock físico y cambiar el estado de armado de los pedidos mediante pistola lectora.
* **ROL-03 (Cliente Web):** Usuario externo autenticado vía JWT. Autorizado para gestionar sus direcciones de envío, visualizar el catálogo y generar órdenes de compra.

---

## 3. Catálogo de Reglas de Negocio (RN)

| Código | Nombre de la Regla | Definición y Restricción Técnica |
| :--- | :--- | :--- |
| **RN-01** | **Normalización Geográfica Estricta** | Las direcciones no admiten texto libre para comunas o regiones. Todo domicilio debe vincularse mediante llave foránea a entidades paramétricas (`REGION` y `COMUNA`) con su respectivo código de cobertura oficial de Chilexpress. |
| **RN-02** | **Jerarquía de Catálogo y Permisos** | Todo producto pertenece obligatoriamente a una `SUBCATEGORIA`, la cual depende de una `CATEGORIA` padre. La mutación de estas tablas está bloqueada a nivel de API para usuarios sin privilegio `is_superuser`. |
| **RN-03** | **Generación Automática de SKU** | Si un producto se registra sin código SKU manual, el motor de base de datos generará un identificador único e inmutable con la estructura `[PREFIJO_CAT]-[PREFIJO_SUBCAT]-[CORRELATIVO_4_DIGITOS]` (ej. `HOG-VEL-0001`). |
| **RN-04** | **Atomicidad de Inventario** | Toda orden de compra o salida de bodega se ejecuta bajo bloques `@transaction.atomic` y bloqueo de fila (`select_for_update`). Si el stock solicitado supera el `stock_actual` de algún ítem, se aborta toda la transacción evitando saldos negativos. |
| **RN-05** | **Privacidad y Cifrado de Datos** | Las credenciales de acceso se almacenan bajo algoritmo hash unidireccional PBKDF2-SHA256. Los datos sensibles de contacto y despacho (`rut`, `telefono`, `calle`, `numero`) están protegidos mediante autorización a nivel de serializador, exigiendo validación de credenciales de administrador o sesión activa autorizada para su desencriptación/visualización en pantalla. |
| **RN-06** | **Dualidad Tributaria (B2C / B2B)** | El perfil del cliente soporta ventas con Boleta (Persona Natural) y Factura (Empresa). Si el pedido requiere factura, se vuelven obligatorios los campos `razon_social` y `giro_comercial`. |

---

## 4. Esquema del Modelo Relacional (Normalizado en 3FN)

Notación formal del esquema relacional de la base de datos `erp_danema`:

* **REGION** (<u>id</u>, nombre, codigo_iso)
* **COMUNA** (<u>id</u>, nombre, codigo_chilexpress, *region_id*)
* **CATEGORIA** (<u>id</u>, nombre, prefijo_sku, descripcion)
* **SUBCATEGORIA** (<u>id</u>, nombre, prefijo_sku, *categoria_id*)
* **PRODUCTO** (<u>id</u>, sku, codigo_barras_ean, nombre, descripcion, precio_venta, costo_unitario, stock_actual, stock_minimo_alerta, peso_kg, largo_cm, ancho_cm, alto_cm, activo, *subcategoria_id*)
* **CLIENTE** (<u>id</u>, *usuario_id*, rut, nombres, apellidos, telefono, tipo_documento_preferido, razon_social, giro_comercial, fecha_registro)
* **DIRECCION_ENVIO** (<u>id</u>, alias, calle, numero, depto_oficina, referencia, es_principal, *cliente_id*, *comuna_id*)
* **PEDIDO** (<u>id</u>, fecha_creacion, fecha_actualizacion, canal_venta, estado, tipo_documento, costo_envio, tracking_chilexpress, *cliente_id*, *direccion_envio_id*, *operador_bodega_id*)
* **DETALLE_PEDIDO** (<u>id</u>, cantidad, precio_unitario_congelado, *pedido_id*, *producto_id*)

*(Nota: <u>Subrayado</u> = Primary Key [PK] | *Cursiva* = Foreign Key [FK])*