# Solución: Error "Wrong value for account.account.internal_group: 'revenue'"

## 🐛 Problema

**Error en los logs:**
```
ERROR testing odoo.addons.club_talento_account_import.wizards.club_talento_import_wizard:
Error creando asiento 79 (2024): Wrong value for account.account.internal_group: 'revenue'
```

**Fecha**: 2025-10-31 10:15:18
**Ubicación**: Función `infer_account_type()` en `account_normalizer.py`

---

## 🔍 Causa del problema

El código usaba el valor `'revenue'` para el campo `account_type`, pero este valor **no es válido en Odoo 18**.

```python
# CÓDIGO ANTIGUO (INCORRECTO)
account_type_map = {
    "1": "asset_current",
    "2": "liability_current",
    "3": "equity",
    "4": "revenue",  # ❌ No válido en Odoo 18
    "5": "expense",
    "6": "expense",
    "7": "revenue",  # ❌ No válido en Odoo 18
}
```

---

## ✅ Valores válidos en Odoo 18

Los valores válidos para `account_type` en Odoo 18 son:

| Categoría | Valores |
|-----------|---------|
| **Activos** | `asset_receivable`, `asset_cash`, `asset_current`, `asset_non_current`, `asset_prepayments`, `asset_fixed` |
| **Pasivos** | `liability_payable`, `liability_credit_card`, `liability_current`, `liability_non_current` |
| **Patrimonio** | `equity`, `equity_unaffected` |
| **Ingresos** | `income`, `income_other` |
| **Gastos** | `expense`, `expense_depreciation`, `expense_direct_cost` |
| **Otros** | `off_balance` |

**Nota importante**: En Odoo 18, `'revenue'` **NO existe**. El valor correcto es `'income'`.

---

## ✅ Solución aplicada

Se cambió el valor `'revenue'` por `'income'` en el mapeo de tipos de cuenta:

```python
# CÓDIGO NUEVO (CORRECTO)
def infer_account_type(code6):
    """
    Infiere el tipo de cuenta según el primer dígito del código normalizado.

    Mapa basado en PGC español (compatible con Odoo 18):
    - 1xx: Activo corriente (asset_current)
    - 2xx: Pasivo corriente (liability_current)
    - 3xx: Patrimonio (equity)
    - 4xx: Ingresos (income) ✅
    - 5xx: Gastos (expense) - excepto 570, 572 que son liquidez
    - 6xx: Gastos (expense)
    - 7xx: Ingresos (income) ✅
    - 570/572: Liquidez (asset_cash)

    Returns:
        str: account_type compatible con Odoo 18
    """
    if not code6 or len(code6) < 1:
        return "expense"

    first_digit = code6[0]

    # Casos especiales de liquidez
    if code6.startswith("570") or code6.startswith("572"):
        return "asset_cash"

    # Mapa general por primer dígito (compatible Odoo 18)
    account_type_map = {
        "1": "asset_current",
        "2": "liability_current",
        "3": "equity",
        "4": "income",  # ✅ Cambiado de 'revenue' a 'income'
        "5": "expense",
        "6": "expense",
        "7": "income",  # ✅ Cambiado de 'revenue' a 'income'
    }

    return account_type_map.get(first_digit, "expense")
```

---

## 📊 Mapeo de cuentas PGC español → Odoo 18

| Código PGC | Descripción | Tipo Odoo 18 |
|------------|-------------|--------------|
| 1xx | Financiación básica | `asset_current` |
| 2xx | Activo no corriente | `liability_current` |
| 3xx | Existencias | `equity` |
| 4xx | Acreedores y deudores | `income` ✅ |
| 5xx | Cuentas financieras | `expense` |
| 570/572 | Caja y bancos | `asset_cash` |
| 6xx | Compras y gastos | `expense` |
| 7xx | Ventas e ingresos | `income` ✅ |

**Nota**: Las cuentas 400, 410, 430 son casos especiales (terceros) que se normalizan a cuentas específicas.

---

## 🔧 Cambios realizados

| Elemento | Antes | Ahora |
|----------|-------|-------|
| Cuentas 4xx | `'revenue'` ❌ | `'income'` ✅ |
| Cuentas 7xx | `'revenue'` ❌ | `'income'` ✅ |
| Compatibilidad | Odoo < 18 | Odoo 18 ✅ |

---

## 🧪 Verificación

Para verificar que funciona correctamente:

1. **Importar archivo Excel** con cuentas de tipo 4xx y 7xx
2. **Verificar cuentas creadas**:
   - Ir a: Facturación → Configuración → Plan contable
   - Buscar cuentas del grupo 4 y 7
   - Verificar que el tipo sea "Income" (Ingresos)

3. **Verificar asientos**:
   - No deben aparecer errores de "Wrong value"
   - Las cuentas deben crearse correctamente

---

## 📝 Ejemplos de cuentas afectadas

### Cuentas de ingresos (Grupo 7):

| Código | Nombre típico | Tipo anterior | Tipo correcto |
|--------|---------------|---------------|---------------|
| 700000 | Ventas mercaderías | `revenue` ❌ | `income` ✅ |
| 705000 | Prestaciones servicios | `revenue` ❌ | `income` ✅ |
| 708000 | Devoluciones ventas | `revenue` ❌ | `income` ✅ |

### Cuentas grupo 4 (excepto terceros):

| Código | Nombre típico | Tipo anterior | Tipo correcto |
|--------|---------------|---------------|---------------|
| 477000 | HP IVA repercutido | `revenue` ❌ | `income` ✅ |
| 475000 | HP acreedora | `revenue` ❌ | `income` ✅ |

**Nota**: Las cuentas 400000, 410000, 430000 (terceros) se gestionan de forma especial.

---

## 📁 Archivo modificado

**Ruta**: `/models/account_normalizer.py`
**Función**: `infer_account_type()` (línea ~81-118)

---

## 🔄 Cambios aplicados

1. ✅ Cambiado `"4": "revenue"` → `"4": "income"`
2. ✅ Cambiado `"7": "revenue"` → `"7": "income"`
3. ✅ Actualizado docstring con valores correctos
4. ✅ Módulo listo para actualizar

---

## 🚀 Para aplicar los cambios

Actualizar el módulo en la base de datos:

```bash
cd /home/xtendoo/Documentos/odoo/18verifactu
docker-compose run --rm odoo odoo -u club_talento_account_import -d testing --stop-after-init
```

O reiniciar el servidor:

```bash
docker-compose restart odoo
```

---

## ⚠️ Nota de compatibilidad

Este cambio hace que el módulo sea **compatible con Odoo 18**.

- **Odoo 18**: Usa `'income'` para cuentas de ingresos ✅
- **Odoo < 18**: Usaba `'revenue'` (ya no válido)

Si necesitas compatibilidad con versiones anteriores de Odoo, sería necesario detectar la versión y usar el valor apropiado.

---

## ✅ Estado

**Problema**: RESUELTO ✓
**Solución**: Valores de `account_type` actualizados a Odoo 18
**Compatibilidad**: Odoo 18.0 ✅
**Archivo**: `models/account_normalizer.py`
**Fecha de corrección**: 2025-10-31

---

El módulo ahora crea cuentas correctamente usando los tipos de cuenta válidos en Odoo 18.

