# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from ..models.account_normalizer import normalize_account, infer_account_type, is_partner_account


class TestAccountNormalizer(TransactionCase):
    """Tests para la normalización de cuentas contables."""

    def test_normalize_partner_accounts(self):
        """Test cuentas de terceros - casos críticos."""
        # Casos exigidos
        self.assertEqual(normalize_account("410.001"), "410000")
        self.assertEqual(normalize_account("430.001"), "430000")
        self.assertEqual(normalize_account("400.009"), "400000")
        self.assertEqual(normalize_account("40000001"), "400000")

        # Casos adicionales de terceros
        self.assertEqual(normalize_account("410"), "410000")
        self.assertEqual(normalize_account("430"), "430000")
        self.assertEqual(normalize_account("400"), "400000")
        self.assertEqual(normalize_account("410001"), "410000")  # 6 dígitos que empieza con 410
        self.assertEqual(normalize_account("43000001"), "430000")

    def test_normalize_long_accounts(self):
        """Test cuentas con >= 6 dígitos."""
        # Casos exigidos
        self.assertEqual(normalize_account("62100001"), "621001")
        self.assertEqual(normalize_account("57000001"), "570001")

        # Casos adicionales
        self.assertEqual(normalize_account("12345678"), "123678")
        self.assertEqual(normalize_account("1234567890"), "123890")

    def test_normalize_short_accounts(self):
        """Test cuentas con < 6 dígitos."""
        # Longitud <= 3
        self.assertEqual(normalize_account("1"), "100000")
        self.assertEqual(normalize_account("12"), "120000")
        self.assertEqual(normalize_account("123"), "123000")

        # Longitud 4-5
        self.assertEqual(normalize_account("1234"), "123400")
        self.assertEqual(normalize_account("12345"), "123450")

    def test_normalize_with_non_digits(self):
        """Test cuentas con caracteres no numéricos."""
        self.assertEqual(normalize_account("410.001"), "410000")
        self.assertEqual(normalize_account("621-001"), "621001")
        self.assertEqual(normalize_account("570 001"), "570001")
        self.assertEqual(normalize_account("ABC123DEF456GHI"), "123456")

    def test_normalize_empty_or_invalid(self):
        """Test casos límite."""
        self.assertEqual(normalize_account(""), "")
        self.assertEqual(normalize_account(None), "")
        self.assertEqual(normalize_account("ABC"), "")
        self.assertEqual(normalize_account("..."), "")

    def test_infer_account_type(self):
        """Test inferencia de tipo de cuenta."""
        # Activos
        self.assertEqual(infer_account_type("123000"), "asset_current")

        # Pasivos
        self.assertEqual(infer_account_type("210000"), "liability_current")

        # Patrimonio
        self.assertEqual(infer_account_type("300000"), "equity")

        # Ingresos
        self.assertEqual(infer_account_type("400000"), "revenue")
        self.assertEqual(infer_account_type("700000"), "revenue")

        # Gastos
        self.assertEqual(infer_account_type("500000"), "expense")
        self.assertEqual(infer_account_type("600000"), "expense")

        # Liquidez (casos especiales)
        self.assertEqual(infer_account_type("570000"), "asset_cash")
        self.assertEqual(infer_account_type("572000"), "asset_cash")

        # Por defecto
        self.assertEqual(infer_account_type("999000"), "expense")
        self.assertEqual(infer_account_type(""), "expense")

    def test_is_partner_account(self):
        """Test detección de cuentas de terceros."""
        # Es cuenta de tercero
        self.assertTrue(is_partner_account("400000"))
        self.assertTrue(is_partner_account("410000"))
        self.assertTrue(is_partner_account("430000"))

        # No es cuenta de tercero
        self.assertFalse(is_partner_account("400001"))
        self.assertFalse(is_partner_account("410001"))
        self.assertFalse(is_partner_account("430001"))
        self.assertFalse(is_partner_account("621001"))
        self.assertFalse(is_partner_account("570001"))

