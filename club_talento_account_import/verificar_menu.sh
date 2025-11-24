#!/bin/bash
# Script de verificación del menú Club Talento Account Import

echo "=== Verificación del menú 'Importar Asientos desde Excel' ==="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar archivo de menú
echo "1. Verificando archivo de menú..."
if [ -f "/home/xtendoo/Documentos/odoo/18verifactu/odoo/custom/src/custom-club-talento/club_talento_account_import/views/club_talento_import_menu.xml" ]; then
    echo -e "${GREEN}✓${NC} Archivo de menú existe"

    # Verificar que tenga el atributo groups
    if grep -q 'groups="account.group_account_user"' "/home/xtendoo/Documentos/odoo/18verifactu/odoo/custom/src/custom-club-talento/club_talento_account_import/views/club_talento_import_menu.xml"; then
        echo -e "${GREEN}✓${NC} Atributo 'groups' configurado correctamente"
    else
        echo -e "${RED}✗${NC} Falta el atributo 'groups' en el menú"
    fi
else
    echo -e "${RED}✗${NC} Archivo de menú no encontrado"
fi

echo ""
echo "2. Verificando manifest..."
if grep -q "views/club_talento_import_menu.xml" "/home/xtendoo/Documentos/odoo/18verifactu/odoo/custom/src/custom-club-talento/club_talento_account_import/__manifest__.py"; then
    echo -e "${GREEN}✓${NC} Archivo de menú incluido en __manifest__.py"
else
    echo -e "${RED}✗${NC} Archivo de menú NO incluido en __manifest__.py"
fi

echo ""
echo "=== Instrucciones para solucionar el problema ==="
echo ""
echo -e "${YELLOW}Para que el menú sea accesible, el usuario debe:${NC}"
echo ""
echo "A) Tener los permisos correctos:"
echo "   - Ir a: Configuración > Usuarios y Empresas > Usuarios"
echo "   - Editar el usuario"
echo "   - En la pestaña 'Derechos de acceso', asegurarse de que tenga:"
echo "     * Facturación / Usuario (mínimo)"
echo "     * o Facturación / Administrador"
echo ""
echo "B) Actualizar el módulo en la base de datos:"
echo "   cd /home/xtendoo/Documentos/odoo/18verifactu"
echo "   docker-compose run --rm odoo odoo -u club_talento_account_import -d [NOMBRE_DB] --stop-after-init"
echo ""
echo "   Reemplazar [NOMBRE_DB] por el nombre de tu base de datos"
echo ""
echo "C) Refrescar el navegador (Ctrl+F5) después de actualizar el módulo"
echo ""
echo -e "${YELLOW}Ubicación del menú en Odoo:${NC}"
echo "   Facturación → Clientes → Importar Asientos desde Excel"
echo ""

