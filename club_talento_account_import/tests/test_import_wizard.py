# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError

try:
    import openpyxl
except ImportError:
    openpyxl = None


class TestImportWizard(TransactionCase):
    """Tests para el wizard de importación."""

    def setUp(self):
        super().setUp()

        # Crear diario de prueba
        self.journal = self.env["account.journal"].create({
            "name": "Test Journal",
            "code": "TEST",
            "type": "general",
        })

        # Crear cuentas base para pruebas
        self.account_400 = self.env["account.account"].create({
            "code": "400000",
            "name": "Proveedores",
            "account_type": "liability_current",
        })

        self.account_410 = self.env["account.account"].create({
            "code": "410000",
            "name": "Acreedores",
            "account_type": "liability_current",
        })

        self.account_430 = self.env["account.account"].create({
            "code": "430000",
            "name": "Clientes",
            "account_type": "asset_receivable",
        })

        self.account_621 = self.env["account.account"].create({
            "code": "621001",
            "name": "Arrendamientos",
            "account_type": "expense",
        })

        self.account_570 = self.env["account.account"].create({
            "code": "570001",
            "name": "Caja",
            "account_type": "asset_cash",
        })

    def _create_test_excel(self, data_by_sheet):
        """
        Crea un archivo Excel de prueba.

        Args:
            data_by_sheet: dict {sheet_name: [list of rows]}
                           Cada row es un dict con claves: Fecha, Asto., Cuenta, etc.

        Returns:
            bytes: Contenido del archivo Excel
        """
        if not openpyxl:
            self.skipTest("openpyxl no está instalado")

        workbook = openpyxl.Workbook()
        workbook.remove(workbook.active)  # Eliminar hoja por defecto

        for sheet_name, rows in data_by_sheet.items():
            sheet = workbook.create_sheet(title=sheet_name)

            # Encabezados
            headers = ["Fecha", "Asto.", "Ord", "Dia", "Cuenta", "Título", "Concepto", "Debe", "Haber"]
            sheet.append(headers)

            # Datos
            for row in rows:
                sheet.append([
                    row.get("Fecha", ""),
                    row.get("Asto.", ""),
                    row.get("Ord", ""),
                    row.get("Dia", ""),
                    row.get("Cuenta", ""),
                    row.get("Título", ""),
                    row.get("Concepto", ""),
                    row.get("Debe", 0),
                    row.get("Haber", 0),
                ])

        # Guardar en bytes
        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def test_import_balanced_move(self):
        """Test importación de asiento que cuadra."""
        # Preparar datos
        data = {
            "2023": [
                {
                    "Fecha": "01-Ene",
                    "Asto.": "1",
                    "Cuenta": "62100001",
                    "Título": "Arrendamiento",
                    "Concepto": "Alquiler local enero",
                    "Debe": 1000.0,
                    "Haber": 0.0,
                },
                {
                    "Fecha": "01-Ene",
                    "Asto.": "1",
                    "Cuenta": "57000001",
                    "Título": "Caja",
                    "Concepto": "Pago alquiler",
                    "Debe": 0.0,
                    "Haber": 1000.0,
                },
            ],
            "2024": [],
            "2025": [],
        }

        excel_content = self._create_test_excel(data)

        # Crear wizard
        wizard = self.env["club.talento.import.wizard"].create({
            "file_data": base64.b64encode(excel_content),
            "file_name": "test.xlsx",
            "journal_id": self.journal.id,
            "create_accounts": True,
            "create_partners": True,
            "post_balanced": True,
        })

        # Ejecutar importación
        wizard.action_import()

        # Verificaciones
        self.assertEqual(len(wizard.move_ids), 1)
        move = wizard.move_ids[0]

        # Verificar estado (debería estar publicado)
        self.assertEqual(move.state, "posted")

        # Verificar líneas
        self.assertEqual(len(move.line_ids), 2)

        # Verificar balance
        total_debit = sum(move.line_ids.mapped("debit"))
        total_credit = sum(move.line_ids.mapped("credit"))
        self.assertEqual(total_debit, 1000.0)
        self.assertEqual(total_credit, 1000.0)

    def test_import_unbalanced_move(self):
        """Test importación de asiento que NO cuadra."""
        # Preparar datos descuadrados
        data = {
            "2023": [
                {
                    "Fecha": "01-Ene",
                    "Asto.": "1",
                    "Cuenta": "621001",
                    "Concepto": "Gasto",
                    "Debe": 1000.0,
                    "Haber": 0.0,
                },
                {
                    "Fecha": "01-Ene",
                    "Asto.": "1",
                    "Cuenta": "570001",
                    "Concepto": "Caja",
                    "Debe": 0.0,
                    "Haber": 900.0,  # Descuadre de 100
                },
            ],
            "2024": [],
            "2025": [],
        }

        excel_content = self._create_test_excel(data)

        # Crear wizard
        wizard = self.env["club.talento.import.wizard"].create({
            "file_data": base64.b64encode(excel_content),
            "file_name": "test.xlsx",
            "journal_id": self.journal.id,
            "create_accounts": True,
            "create_partners": True,
            "post_balanced": False,
        })

        # Ejecutar importación
        wizard.action_import()

        # Verificaciones
        self.assertEqual(len(wizard.move_ids), 1)
        move = wizard.move_ids[0]

        # Verificar estado (debería estar en borrador)
        self.assertEqual(move.state, "draft")

    def test_create_partner_for_partner_account(self):
        """Test creación de partner para cuentas de terceros."""
        # Preparar datos con cuenta de tercero
        data = {
            "2023": [
                {
                    "Fecha": "01-Ene",
                    "Asto.": "1",
                    "Cuenta": "410.001",  # Normaliza a 410000
                    "Título": "ACME SL",
                    "Concepto": "Factura 123",
                    "Debe": 0.0,
                    "Haber": 500.0,
                },
                {
                    "Fecha": "01-Ene",
                    "Asto.": "1",
                    "Cuenta": "621001",
                    "Concepto": "Gasto",
                    "Debe": 500.0,
                    "Haber": 0.0,
                },
            ],
            "2024": [],
            "2025": [],
        }

        excel_content = self._create_test_excel(data)

        # Crear wizard
        wizard = self.env["club.talento.import.wizard"].create({
            "file_data": base64.b64encode(excel_content),
            "file_name": "test.xlsx",
            "journal_id": self.journal.id,
            "create_accounts": True,
            "create_partners": True,
            "post_balanced": True,
        })

        # Ejecutar importación
        wizard.action_import()

        # Verificar que se creó el partner
        partner = self.env["res.partner"].search([("name", "=", "ACME SL")])
        self.assertTrue(partner)

        # Verificar que la línea tiene el partner asignado
        move = wizard.move_ids[0]
        partner_line = move.line_ids.filtered(lambda l: l.account_id.code == "410000")
        self.assertEqual(partner_line.partner_id, partner)

    def test_missing_accounts_without_create(self):
        """Test fallo cuando falta cuenta y create_accounts=False."""
        # Preparar datos con cuenta inexistente
        data = {
            "2023": [
                {
                    "Fecha": "01-Ene",
                    "Asto.": "1",
                    "Cuenta": "999999",  # Cuenta que no existe
                    "Concepto": "Test",
                    "Debe": 100.0,
                    "Haber": 0.0,
                },
                {
                    "Fecha": "01-Ene",
                    "Asto.": "1",
                    "Cuenta": "570001",
                    "Concepto": "Caja",
                    "Debe": 0.0,
                    "Haber": 100.0,
                },
            ],
            "2024": [],
            "2025": [],
        }

        excel_content = self._create_test_excel(data)

        # Crear wizard con create_accounts=False
        wizard = self.env["club.talento.import.wizard"].create({
            "file_data": base64.b64encode(excel_content),
            "file_name": "test.xlsx",
            "journal_id": self.journal.id,
            "create_accounts": False,
            "create_partners": True,
            "post_balanced": False,
        })

        # Debe fallar
        with self.assertRaises(ValidationError):
            wizard.action_import()

    def test_multiple_years(self):
        """Test importación de múltiples años."""
        # Preparar datos para varios años
        data = {
            "2023": [
                {
                    "Fecha": "01-Ene",
                    "Asto.": "1",
                    "Cuenta": "621001",
                    "Concepto": "Gasto 2023",
                    "Debe": 100.0,
                    "Haber": 0.0,
                },
                {
                    "Fecha": "01-Ene",
                    "Asto.": "1",
                    "Cuenta": "570001",
                    "Concepto": "Caja",
                    "Debe": 0.0,
                    "Haber": 100.0,
                },
            ],
            "2024": [
                {
                    "Fecha": "01-Feb",
                    "Asto.": "1",
                    "Cuenta": "621001",
                    "Concepto": "Gasto 2024",
                    "Debe": 200.0,
                    "Haber": 0.0,
                },
                {
                    "Fecha": "01-Feb",
                    "Asto.": "1",
                    "Cuenta": "570001",
                    "Concepto": "Caja",
                    "Debe": 0.0,
                    "Haber": 200.0,
                },
            ],
            "2025": [],
        }

        excel_content = self._create_test_excel(data)

        # Crear wizard
        wizard = self.env["club.talento.import.wizard"].create({
            "file_data": base64.b64encode(excel_content),
            "file_name": "test.xlsx",
            "journal_id": self.journal.id,
            "create_accounts": True,
            "create_partners": True,
            "post_balanced": True,
        })

        # Ejecutar importación
        wizard.action_import()

        # Verificar que se crearon asientos para ambos años
        self.assertEqual(len(wizard.move_ids), 2)

        # Verificar fechas
        dates = wizard.move_ids.mapped("date")
        self.assertTrue(any(d.year == 2023 for d in dates))
        self.assertTrue(any(d.year == 2024 for d in dates))

