# Club Talento Account Import

[![License: AGPL-3](https://img.shields.io/badge/License-AGPL%203-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

Módulo de importación de asientos contables desde Excel para Odoo 18.0

## Características

- ✅ Importación masiva desde archivos Excel (.xlsx)
- ✅ Soporte para múltiples años automático (extrae el año de las fechas)
- ✅ Procesa todas las hojas del archivo Excel automáticamente
- ✅ Normalización automática de cuentas contables a 6 dígitos
- ✅ Creación automática de cuentas y contactos
- ✅ Detección y enlace de cuentas de terceros (400, 410, 430)
- ✅ Validación de balance automática
- ✅ Publicación opcional de asientos que cuadren
- ✅ Auditoría completa en chatter
- ✅ Resumen detallado de la importación

## Instalación

1. Clonar el repositorio en `custom-club-talento`:

```bash
cd /path/to/odoo/custom-club-talento
```

2. Instalar dependencias:

```bash
pip install openpyxl
```

3. Actualizar la lista de módulos en Odoo
4. Instalar el módulo "Club Talento Account Import"

## Uso

### Preparación del archivo Excel

El archivo Excel puede contener una o múltiples hojas. El módulo procesará automáticamente todas las hojas encontradas.

**Formato de fecha soportado:** Las fechas deben incluir el año completo o abreviado (ej: 23/02/23 o 23/02/2023). El año se extrae automáticamente de cada fecha.

Cada hoja debe tener las siguientes columnas:

| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| Fecha | Fecha de la línea con año | 23/02/23 |
| Asto. | Número de asiento | 1 |
| Cuenta | Código de cuenta | 410.001 |
| Título | Descripción / Nombre del contacto | ACME SL |
| Concepto | Descripción de la línea | Factura 123 |
| Debe | Importe debe | 1.000,00 |
| Haber | Importe haber | 0,00 |

**Formatos de fecha soportados:**
- `23/02/23` - día/mes/año (2 dígitos)
- `23/02/2023` - día/mes/año (4 dígitos)
- `2023-02-23` - año-mes-día (ISO)
- `23-02-2023` - día-mes-año con guiones

**Formatos de importe soportados:**
- Español: `1.000,00` (punto como separador de miles, coma como decimal)
- Internacional: `1000.00` (punto como decimal)

### Importación

1. Ir a **Contabilidad > Importaciones > Importar Diario Club Talento**
2. Subir el archivo Excel
3. Configurar las opciones:
   - Compañía
   - Diario destino
   - Crear cuentas automáticamente
   - Crear contactos automáticamente
   - Publicar asientos que cuadren
4. Hacer clic en **Importar**
5. Revisar el resumen y los asientos creados

## Reglas de normalización

### Cuentas largas (>= 6 dígitos)

Se toman los 3 primeros + los 3 últimos dígitos:

- `40000001` → **400000**
- `62100001` → **621001**

### Cuentas cortas (< 6 dígitos)

- `410` → **410000**
- `4101` → **410100**

### Regla especial: Cuentas de terceros

Las cuentas que empiezan por 400, 410 o 430 se normalizan a:

- `400xxx` → **400000** (Proveedores)
- `410xxx` → **410000** (Acreedores)
- `430xxx` → **430000** (Clientes)

**Ejemplos críticos:**

- `410.001` → **410000** ✅
- `430.001` → **430000** ✅
- `400.009` → **400000** ✅

## Tests

El módulo incluye una batería completa de tests:

```bash
odoo-bin -c odoo.conf -i club_talento_account_import --test-enable --stop-after-init
```

### Tests incluidos

- ✅ Tests de normalización de cuentas
- ✅ Tests de inferencia de tipo de cuenta
- ✅ Tests de importación de asientos balanceados
- ✅ Tests de importación de asientos desbalanceados
- ✅ Tests de creación de partners
- ✅ Tests de creación de cuentas
- ✅ Tests de múltiples años

## Documentación

La documentación completa está disponible en:

- `readme/USAGE.rst`: Guía de uso detallada
- `static/description/index.html`: Documentación HTML

## Autor

**Xtendoo**

- GitHub: https://github.com/xtendoo-corporation/custom-club-talento

## Licencia

AGPL-3

## Contribuciones

Las contribuciones son bienvenidas. Por favor, crea un issue o pull request.

## Soporte

Para soporte, por favor crea un issue en GitHub.

