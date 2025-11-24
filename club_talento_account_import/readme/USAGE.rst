=====
Usage
=====

Instalación
===========

1. Instalar el módulo desde Apps > Buscar "Club Talento Account Import" > Instalar

2. Asegurarse de tener instalado openpyxl:

   .. code-block:: bash

      pip install openpyxl


Preparación del archivo Excel
==============================

El archivo Excel debe tener tres hojas llamadas exactamente: **2023**, **2024**, **2025**

Cada hoja debe contener las siguientes columnas (la fila de encabezados se detecta automáticamente):

- **Fecha**: Formato 01-Oct. o 01/10/2023
- **Asto.**: Número de asiento legacy
- **Ord**: Orden (opcional)
- **Dia**: Día (opcional)
- **Cuenta**: Código de cuenta (puede tener puntos, guiones, etc.)
- **Título**: Descripción corta / Nombre del contacto para cuentas de terceros
- **Concepto**: Descripción extendida de la línea
- **Debe**: Importe debe
- **Haber**: Importe haber


Ejemplo de datos:

+----------+-------+-----+-----+---------+------------------+----------------------+--------+--------+
| Fecha    | Asto. | Ord | Dia | Cuenta  | Título           | Concepto             | Debe   | Haber  |
+==========+=======+=====+=====+=========+==================+======================+========+========+
| 01-Oct.  | 1     | 1   | 1   | 410.001 | ACME SL          | Factura 123          | 0      | 1000   |
+----------+-------+-----+-----+---------+------------------+----------------------+--------+--------+
| 01-Oct.  | 1     | 2   | 1   | 621.001 | Arrendamiento    | Alquiler local       | 1000   | 0      |
+----------+-------+-----+-----+---------+------------------+----------------------+--------+--------+


Uso del asistente
=================

1. Ir a **Contabilidad > Importaciones > Importar Diario Club Talento**

2. Configurar el asistente:

   - **Archivo Excel**: Subir el archivo .xlsx
   - **Compañía**: Seleccionar la compañía (por defecto la actual)
   - **Diario**: Seleccionar el diario destino (por defecto "Operaciones diversas")
   - **Crear cuentas si no existen**: Si está marcado, crea automáticamente las cuentas que falten
   - **Crear contactos si no existen**: Si está marcado, crea automáticamente los contactos
   - **Publicar asientos que cuadren**: Si está marcado, publica automáticamente los asientos cuyo balance sea cero

3. Hacer clic en **Importar**

4. El asistente mostrará un resumen con:

   - Número de asientos creados por año
   - Asientos publicados vs. en borrador
   - Contactos creados
   - Cuentas creadas
   - Advertencias y errores

5. Al finalizar, se abre una vista con los asientos importados


Reglas de normalización de cuentas
===================================

Todas las cuentas se normalizan a **6 dígitos**:

**Cuentas largas (>= 6 dígitos)**

- Se toman los 3 primeros + los 3 últimos dígitos
- Ejemplo: 40000001 → 400000
- Ejemplo: 62100001 → 621001

**Cuentas cortas (< 6 dígitos)**

- Si tiene <= 3 dígitos: se añaden 000 al final

  - 410 → 410000

- Si tiene 4-5 dígitos: se completa hasta 3 dígitos finales con ceros

  - 4101 → 410100
  - 43001 → 430010

**Regla especial: Cuentas de terceros**

Las cuentas que empiezan por 400, 410 o 430 se fuerzan a:

- 400xxx → **400000** (Proveedores)
- 410xxx → **410000** (Acreedores)
- 430xxx → **430000** (Clientes)

Ejemplos:

- 410.001 → 410000
- 430.001 → 430000
- 400.009 → 400000


Cuentas de terceros y contactos
================================

Si la cuenta normalizada es **400000**, **410000** o **430000**, la línea debe tener un contacto (partner).

- El nombre del contacto se toma de la columna **Título**
- Si el contacto no existe, se crea automáticamente (si la opción está activa)
- El contacto se enlaza en la línea del asiento


Validación de balance
======================

Cada asiento se valida para verificar que el balance sea cero (debe = haber).

- Si cuadra y la opción "Publicar asientos que cuadren" está activa → se publica automáticamente
- Si NO cuadra → se deja en borrador y se registra un mensaje en el chatter con la diferencia


Auditoría
=========

En el chatter de cada asiento importado se registra:

- Año de origen
- Número de asiento legacy (Asto.)
- Fecha
- Número de líneas
- Balance total
- Advertencias (si las hay)


Solución de problemas
=====================

**Error: "El módulo 'openpyxl' no está instalado"**

Instalar openpyxl:

.. code-block:: bash

   pip install openpyxl

**Error: "Faltan las siguientes hojas en el archivo: ..."**

El archivo Excel debe tener exactamente tres hojas: 2023, 2024, 2025

**Error: "Faltan las siguientes cuentas y la opción 'Crear cuentas...' está desactivada"**

- Activar la opción "Crear cuentas si no existen", o
- Crear manualmente las cuentas faltantes antes de importar

**Advertencia: "Asiento X no cuadra. Diferencia: YYY"**

El asiento se crea en borrador. Revisar las líneas y ajustar manualmente.

**Advertencia: "No se pudo parsear fecha"**

El formato de fecha no se pudo interpretar. Se usa 01/01/YYYY como fallback.
Revisar el formato en el Excel (debe ser 01-Oct. o 01/10/2023).

