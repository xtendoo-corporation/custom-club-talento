# Instalación del módulo Club Talento - IBAN en Factura PDF

## Pasos para instalar el módulo:

### 1. Verificar que el módulo está en la ruta correcta
El módulo ya está ubicado en:
```
/home/odoo/Escritorio/odoo/odoo18/odoo/custom/src/custom-club-talento/club_talento_invoice_iban/
```

### 2. Actualizar la lista de módulos en Odoo
Accede a Odoo con permisos de administrador y:
- Ve a **Aplicaciones** (Apps)
- Haz clic en el menú de tres puntos (⋮)
- Selecciona **Actualizar lista de aplicaciones**
- Confirma la actualización

### 3. Buscar e instalar el módulo
- En la lista de aplicaciones, quita el filtro "Aplicaciones"
- Busca: **"Club Talento - IBAN en Factura PDF"** o **"club_talento_invoice_iban"**
- Haz clic en **Instalar**

### 4. Verificar la instalación
Una vez instalado, genera una factura de cliente PDF que cumpla con las condiciones:
- Tipo: Factura de cliente (out_invoice)
- Método de pago: Domiciliación bancaria SEPA
- Cliente con IBAN configurado

El IBAN debería aparecer en la parte derecha del PDF, justo después de la información de dirección del cliente.

## Estructura del módulo creado:

```
club_talento_invoice_iban/
├── __init__.py                           # Archivo de inicialización Python
├── __manifest__.py                       # Manifiesto del módulo con dependencias
├── README.md                            # Documentación del módulo
├── static/
│   └── description/
│       └── icon.png                     # Ícono del módulo
└── views/
    └── report_invoice_document.xml      # Herencia de la plantilla PDF
```

## Código QWeb implementado:

El fragmento QWeb que se implementó hereda la plantilla `account.report_invoice_document` y agrega:

```xml
<div class="row mt-3" t-if="o.move_type == 'out_invoice' and o.payment_mode_id and o.payment_mode_id.payment_method_code == 'sepa_direct_debit'">
    <div class="col-12 text-end">
        <t t-if="o.partner_id.bank_ids">
            <t t-set="partner_bank" t-value="o.partner_id.bank_ids.filtered(lambda b: b.acc_type == 'iban')[:1]"/>
            <t t-if="partner_bank and partner_bank.acc_number">
                <span t-field="partner_bank.acc_number"/>
            </t>
        </t>
    </div>
</div>
```

### Explicación del código:

1. **Condición principal**: Solo se ejecuta si:
   - `o.move_type == 'out_invoice'`: Es una factura de cliente
   - `o.payment_mode_id`: Tiene un método de pago definido
   - `o.payment_mode_id.payment_method_code == 'sepa_direct_debit'`: El método es domiciliación SEPA

2. **Alineación**: `text-end` coloca el IBAN a la derecha

3. **Seguridad**: Verifica que:
   - El cliente tenga cuentas bancarias (`o.partner_id.bank_ids`)
   - Exista al menos una cuenta de tipo IBAN
   - La cuenta tenga número de cuenta configurado

4. **Solo IBAN**: Imprime únicamente el número de cuenta sin texto adicional

## Notas importantes:

- El módulo depende de `account_banking_sepa_direct_debit` (OCA)
- Si este módulo no está instalado, deberás instalarlo primero
- El código es seguro y no genera errores si el cliente no tiene IBAN
