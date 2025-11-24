#!/bin/bash
# Script de verificación del módulo club_talento_account_import

echo "=========================================="
echo "VERIFICACIÓN DEL MÓDULO"
echo "club_talento_account_import v18.0.1.0.0"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contador de errores
ERRORS=0

# Función para verificar archivo
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1 (FALTA)"
        ERRORS=$((ERRORS+1))
    fi
}

# Función para verificar directorio
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
    else
        echo -e "${RED}✗${NC} $1/ (FALTA)"
        ERRORS=$((ERRORS+1))
    fi
}

echo "1. Verificando estructura de directorios..."
echo "-------------------------------------------"
check_dir "models"
check_dir "wizards"
check_dir "views"
check_dir "security"
check_dir "tests"
check_dir "readme"
check_dir "static"
check_dir "static/description"
check_dir "i18n"
echo ""

echo "2. Verificando archivos principales..."
echo "---------------------------------------"
check_file "__init__.py"
check_file "__manifest__.py"
check_file "README.md"
check_file "LICENSE"
echo ""

echo "3. Verificando modelos..."
echo "-------------------------"
check_file "models/__init__.py"
check_file "models/account_normalizer.py"
echo ""

echo "4. Verificando wizards..."
echo "-------------------------"
check_file "wizards/__init__.py"
check_file "wizards/club_talento_import_wizard.py"
check_file "wizards/club_talento_import_wizard_views.xml"
echo ""

echo "5. Verificando seguridad..."
echo "---------------------------"
check_file "security/ir.model.access.csv"
echo ""

echo "6. Verificando tests..."
echo "-----------------------"
check_file "tests/__init__.py"
check_file "tests/test_account_normalizer.py"
check_file "tests/test_import_wizard.py"
echo ""

echo "7. Verificando documentación..."
echo "--------------------------------"
check_file "readme/USAGE.rst"
check_file "static/description/index.html"
check_file "static/description/icon.png"
check_file "INSTALLATION.md"
check_file "CHANGELOG.md"
echo ""

echo "8. Verificando sintaxis Python..."
echo "----------------------------------"
for file in $(find . -name "*.py" -not -path "*/__pycache__*"); do
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (ERROR DE SINTAXIS)"
        ERRORS=$((ERRORS+1))
    fi
done
echo ""

echo "9. Verificando sintaxis XML..."
echo "-------------------------------"
for file in $(find . -name "*.xml"); do
    if xmllint --noout "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${YELLOW}⚠${NC} $file (xmllint no disponible o error)"
    fi
done
echo ""

echo "10. Verificando dependencias Python..."
echo "---------------------------------------"
if python3 -c "import openpyxl" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} openpyxl instalado"
else
    echo -e "${YELLOW}⚠${NC} openpyxl no instalado (requerido para funcionamiento)"
fi
echo ""

echo "11. Estadísticas del módulo..."
echo "-------------------------------"
echo "Archivos Python: $(find . -name "*.py" -not -path "*/__pycache__*" | wc -l)"
echo "Archivos XML: $(find . -name "*.xml" | wc -l)"
echo "Archivos de tests: $(find . -path "*/tests/test_*.py" | wc -l)"
echo "Líneas de código Python: $(find . -name "*.py" -not -path "*/__pycache__*" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')"
echo "Tamaño total: $(du -sh . 2>/dev/null | awk '{print $1}')"
echo ""

echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}VERIFICACIÓN EXITOSA ✓${NC}"
    echo "El módulo está completo y listo para instalar."
else
    echo -e "${RED}VERIFICACIÓN CON ERRORES ✗${NC}"
    echo "Encontrados $ERRORS errores. Revise los archivos marcados."
fi
echo "=========================================="
echo ""

echo "Próximos pasos:"
echo "1. Instalar openpyxl: pip3 install openpyxl"
echo "2. Actualizar lista de módulos en Odoo"
echo "3. Instalar módulo desde Apps"
echo "4. Ejecutar tests: odoo-bin --test-enable -i club_talento_account_import"
echo ""

exit $ERRORS

