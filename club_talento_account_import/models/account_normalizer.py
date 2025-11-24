# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re


def normalize_account(raw):
    """
    Normaliza una cuenta contable a 6 dígitos según las reglas del PGC.

    Reglas:
    1. Limpia dejando solo dígitos
    2. Si longitud >= 6: usa los 3 primeros + los 3 últimos
    3. Si longitud < 6:
       - Si <= 3: tres primeros + '000'
       - Si 4-5: tres primeros + resto rellenado a 3 con ceros
    4. Regla especial terceros:
       - 400* → 400000
       - 410* → 410000
       - 430* → 430000

    Ejemplos:
        normalize_account("410.001") -> "410000"
        normalize_account("430.001") -> "430000"
        normalize_account("400.009") -> "400000"
        normalize_account("40000001") -> "400000"
        normalize_account("62100001") -> "621001"
        normalize_account("57000001") -> "570001"

    Args:
        raw (str): Código de cuenta sin normalizar

    Returns:
        str: Código normalizado de 6 dígitos o cadena vacía si no hay dígitos
    """
    # 1) Limpiar - dejar solo dígitos
    digits = re.sub(r"\D+", "", raw or "")
    if not digits:
        return ""

    # 2) Normalizar a 6 dígitos
    if len(digits) >= 6:
        code6 = digits[:3] + digits[-3:]
    else:
        if len(digits) <= 3:
            code6 = digits[:3].ljust(3, '0') + '000'
        else:
            head = digits[:3]
            tail = digits[3:]
            tail = tail.ljust(3, '0')[:3]
            code6 = head + tail

    # 3) Regla especial para cuentas de terceros
    if code6.startswith("400"):
        return "400000"
    if code6.startswith("410"):
        return "410000"
    if code6.startswith("430"):
        return "430000"

    return code6


def infer_account_type(code6):
    """
    Infiere el tipo de cuenta según el primer dígito del código normalizado.

    Mapa basado en PGC español (compatible con Odoo 18):
    - 1xx: Activo corriente (asset_current)
    - 2xx: Pasivo corriente (liability_current)
    - 3xx: Patrimonio (equity)
    - 4xx: Ingresos (income) - excepto 400, 410, 430 que son terceros
    - 5xx: Gastos (expense) - excepto 570, 572 que son liquidez
    - 6xx: Gastos (expense)
    - 7xx: Ingresos (income)
    - 570/572: Liquidez (asset_cash)

    Args:
        code6 (str): Código normalizado de 6 dígitos

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


def is_partner_account(code6):
    """
    Determina si una cuenta normalizada corresponde a un tercero.

    Args:
        code6 (str): Código normalizado de 6 dígitos

    Returns:
        bool: True si es cuenta de tercero (400000, 410000, 430000)
    """
    return code6 in ("400000", "410000", "430000")

