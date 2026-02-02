# Club Talento - IBAN en Factura PDF

## Descripción

Este módulo personalizado para Odoo 18 Enterprise modifica la plantilla PDF de facturas de cliente para mostrar el IBAN del cliente cuando se utiliza uno de los **métodos de pago configurados en Ajustes de Contabilidad**.

## Funcionalidad

El módulo imprime el **IBAN del cliente** en el PDF de la factura, alineado a la derecha, justo después de la información de dirección del cliente, **solo cuando se cumplen las siguientes condiciones**:

1. El documento es una **factura de cliente** (`out_invoice`)
2. El **método de pago** de la factura está en la lista de **métodos configurados en Ajustes**
3. El cliente tiene configurado un IBAN en sus cuentas bancarias

## Configuración

1. Ir a **Contabilidad → Configuración → Ajustes**
2. Buscar el bloque **"IBAN en Factura PDF"** (después de "Pagos de cliente")
3. En el campo **"Métodos de pago"**, seleccionar los métodos de pago para los cuales se debe mostrar el IBAN
4. Guardar los ajustes

## Características técnicas

- **Hereda**: `account.report_invoice_document` y `res.config.settings`
- **Posición del IBAN**: A la derecha, después de la información de dirección
- **Validación**: No muestra errores si el cliente no tiene IBAN configurado
- **Formato**: Solo el número IBAN, sin texto adicional
- **Configuración por compañía**: Cada compañía puede tener su propia configuración

## Dependencias

- `account`: Módulo de contabilidad de Odoo
- `account_payment_mode`: Módulo de modos de pago (OCA)

## Instalación

1. Colocar el módulo en la ruta de addons personalizados
2. Actualizar la lista de módulos
3. Instalar el módulo "Club Talento - IBAN en Factura PDF"
4. Configurar los métodos de pago en Ajustes de Contabilidad

## Uso

1. Ve a **Contabilidad → Configuración → Ajustes**
2. En el bloque **"IBAN en Factura PDF"**, añade los métodos de pago deseados
3. Guarda los ajustes
4. Crea una factura con uno de esos métodos de pago
5. Al generar el PDF, aparecerá el IBAN del cliente a la derecha

## Autor

- Xtendoo

## Licencia

AGPL-3.0
