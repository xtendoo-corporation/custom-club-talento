# Configuración de Compañía y Diario en el Wizard de Importación

## ✅ Cambios Realizados

Se ha modificado el wizard de importación para que:

1. **El diario se selecciona manualmente** en el wizard (ya estaba implementado)
2. **La compañía se hereda del contexto** del usuario actual

---

## 🔧 Implementación

### Código Modificado

**Antes:**
```python
# ❌ Company_id explícito en el move
move_vals = {
    "journal_id": self.journal_id.id,
    "date": fecha,
    "ref": f"Importado - Año {year} - Asto. {asto}",
    "company_id": self.company_id.id,  # ❌ Explícito
    "line_ids": move_lines,
}

move = self.env["account.move"].create(move_vals)
```

**Ahora:**
```python
# ✅ Company se hereda del contexto
move_vals = {
    "journal_id": self.journal_id.id,
    "date": fecha,
    "ref": f"Importado - Año {year} - Asto. {asto}",
    "line_ids": move_lines,  # ✅ Sin company_id
}

move = self.env["account.move"].with_company(self.company_id).create(move_vals)
```

---

## 🎯 Funcionamiento

### 1. Selección de Compañía

El wizard tiene un campo `company_id` que:
- **Valor por defecto**: Compañía actual del usuario (`self.env.company`)
- **Modificable**: El usuario puede cambiar la compañía en el wizard
- **Dominio del diario**: Se filtra por la compañía seleccionada

```python
company_id = fields.Many2one(
    "res.company",
    string="Compañía",
    required=True,
    default=lambda self: self.env.company  # ✅ Compañía actual
)
```

### 2. Selección de Diario

El diario se filtra por la compañía seleccionada:

```python
journal_id = fields.Many2one(
    "account.journal",
    string="Diario",
    required=True,
    domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
    help="Diario donde se crearán los asientos"
)
```

### 3. Creación de Asientos

Los asientos se crean usando `with_company()`:

```python
# ✅ Usa el contexto de la compañía seleccionada
move = self.env["account.move"].with_company(self.company_id).create(move_vals)
```

### 4. Creación de Cuentas

Las cuentas también usan el contexto de compañía:

```python
# ✅ Busca y crea cuentas en el contexto de la compañía
account = self.env["account.account"].with_company(self.company_id).search([
    ("code", "=", code6),
], limit=1)

account = self.env["account.account"].with_company(self.company_id).create({
    "code": code6,
    "name": name or f"Cuenta {code6}",
    "account_type": account_type,
})
```

---

## 📋 Flujo de Uso

1. **Usuario abre el wizard**:
   - Compañía por defecto: Compañía actual del usuario
   - Diario por defecto: Primer diario general de esa compañía

2. **Usuario puede cambiar la compañía** (opcional):
   - Al cambiar la compañía, se actualiza la lista de diarios disponibles
   - Método `_onchange_company_id()` se ejecuta automáticamente

3. **Usuario selecciona el diario** (requerido):
   - Solo se muestran diarios de tipo "general"
   - Filtrados por la compañía seleccionada

4. **Usuario carga el archivo y hace clic en "Importar"**:
   - Todos los asientos se crean en la compañía seleccionada
   - Todas las cuentas se crean/buscan en esa compañía
   - El diario seleccionado determina la compañía final del asiento

---

## 🎨 Interfaz del Wizard

```
┌─────────────────────────────────────────────┐
│  Importar Asientos desde Excel              │
├─────────────────────────────────────────────┤
│                                             │
│  📁 Archivo:  [Seleccionar archivo...]      │
│                                             │
│  🏢 Compañía: [Compañía Actual ▼]          │
│               (Cambiable)                   │
│                                             │
│  📓 Diario:   [Operaciones Diversas ▼]     │
│               (Filtrado por compañía)       │
│                                             │
│  ☑ Crear cuentas si no existen             │
│  ☑ Crear contactos si no existen           │
│  ☐ Publicar asientos que cuadren           │
│                                             │
│  [Importar]  [Cerrar]                       │
└─────────────────────────────────────────────┘
```

---

## ✅ Ventajas de esta Implementación

| Aspecto | Beneficio |
|---------|-----------|
| **Flexibilidad** | ✅ Usuario puede elegir compañía y diario |
| **Contexto correcto** | ✅ Usa `with_company()` de forma consistente |
| **Multi-compañía** | ✅ Funciona correctamente en entornos multi-compañía |
| **Validación** | ✅ El diario pertenece a la compañía seleccionada |
| **Herencia** | ✅ La compañía se hereda del diario automáticamente |

---

## 🔍 Verificación

Para verificar que funciona correctamente:

1. **Cambiar la compañía en el wizard**:
   - Verificar que la lista de diarios se actualiza
   - Solo se muestran diarios de la compañía seleccionada

2. **Importar asientos**:
   - Verificar que los asientos se crean en la compañía correcta
   - Verificar que las cuentas se crean en la compañía correcta
   - Verificar que el diario seleccionado aparece en los asientos

3. **Revisar asientos creados**:
   ```
   Campo               | Valor
   --------------------|------------------------
   Compañía            | Compañía seleccionada
   Diario              | Diario seleccionado
   Referencia          | "Importado - Año X - Asto. Y"
   ```

---

## 📝 Código Relevante

### Campos del Wizard

```python
company_id = fields.Many2one(
    "res.company",
    string="Compañía",
    required=True,
    default=lambda self: self.env.company  # ✅ Compañía actual
)

journal_id = fields.Many2one(
    "account.journal",
    string="Diario",
    required=True,
    domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
    help="Diario donde se crearán los asientos"
)
```

### OnChange de Compañía

```python
@api.onchange("company_id")
def _onchange_company_id(self):
    """Actualiza el dominio del diario cuando cambia la compañía."""
    if self.company_id:
        journal = self.env["account.journal"].search([
            ("type", "=", "general"),
            ("company_id", "=", self.company_id.id),
        ], limit=1)
        if journal:
            self.journal_id = journal
```

### Creación de Asiento

```python
move = self.env["account.move"].with_company(self.company_id).create(move_vals)
```

---

## ✅ Estado

**Implementación**: COMPLETADA ✓
**Funcionamiento**: El wizard permite seleccionar diario y usa la compañía actual
**Compañía**: Se hereda del contexto `with_company(self.company_id)`
**Diario**: Seleccionable manualmente, filtrado por compañía
**Fecha**: 2025-10-31

---

El wizard está configurado correctamente para trabajar con la compañía seleccionada actualmente y permitir la selección manual del diario.

