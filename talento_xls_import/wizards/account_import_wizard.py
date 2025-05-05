# Añadir esta dependencia al inicio del archivo
from email.policy import default

import xlrd
import base64
import logging
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountImportWizard(models.TransientModel):
    _name = "talento.account.import.wizard"

    @api.model
    def _default_journal(self):
        return self.env['account.journal'].search([('type', '=', 'general')], limit=1)

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string="Diario contable",
        domain=[('type', '=', 'general')],
        default=_default_journal,
        help="Diario donde se crearán los asientos contables",
    )
    excel_file = fields.Binary(
        string="Archivo Excel de apuntes contables",
    )
    excel_file_name = fields.Char(
        string="Nombre del archivo Excel",
    )

    def action_import(self):
        """Import partners and/or accounting entries from files."""
        message = ""
        entries_created = 0

        if self.excel_file:
            try:
                entries_result = self._import_from_excel()
                entries_created = entries_result.get('entries_created', 0)
                partners_created = entries_result.get('partners_created', 0)
                message += _("%s asientos contables creados. %s contactos creados. ") % (entries_created, partners_created)
            except Exception as e:
                raise UserError(_("Error al procesar el archivo Excel: %s") % str(e))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Importación exitosa"),
                "message": message,
                "sticky": False,
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},
            }
        }

    def _import_from_excel(self):
        """Importa apuntes contables desde un archivo Excel."""
        entries_created = 0
        partners_created = 0
        account_move_obj = self.env['account.move']

        # Decodificar el archivo Excel
        excel_data = base64.b64decode(self.excel_file)
        book = xlrd.open_workbook(file_contents=excel_data)
        sheet = book.sheet_by_index(0)

        # Inicializamos variables para el asiento actual
        current_entry_number = None
        current_entry_date = None
        current_entry_lines = []

        # Recorrer las filas del Excel (saltando la cabecera)
        for row_idx in range(1, sheet.nrows):
            row = sheet.row_values(row_idx)

            # Extraer datos de las columnas
            try:
                date_value = row[0]
                if isinstance(date_value, float):  # Excel almacena fechas como números flotantes
                    date_tuple = xlrd.xldate_as_tuple(date_value, book.datemode)
                    date_str = f"{date_tuple[2]:02d}/{date_tuple[1]:02d}/{date_tuple[0]}"
                else:
                    date_str = date_value

                entry_number = int(row[1])
                account_code = str(int(row[4])) if isinstance(row[4], float) else str(row[4])
                title = row[5]
                concept = row[6]

                # Procesar debe y haber
                debit = float(row[7]) if row[7] and not isinstance(row[7], str) else 0.0
                if isinstance(row[7], str) and row[7].strip():
                    debit = self._parse_amount(row[7])

                credit = float(row[8]) if len(row) > 8 and row[8] and not isinstance(row[8], str) else 0.0
                if len(row) > 8 and isinstance(row[8], str) and row[8].strip():
                    credit = self._parse_amount(row[8])

                # Si cambia el número de asiento, procesamos el asiento anterior
                if current_entry_number is not None and current_entry_number != entry_number:
                    self._create_excel_accounting_entry(
                        current_entry_date,
                        current_entry_number,
                        current_entry_lines
                    )
                    entries_created += 1
                    current_entry_lines = []

                # Actualizar el número de asiento actual
                current_entry_number = entry_number

                # Parsear la fecha
                if isinstance(date_str, str):
                    try:
                        current_entry_date = datetime.strptime(date_str, "%d/%m/%y").date()
                    except ValueError:
                        try:
                            current_entry_date = datetime.strptime(date_str, "%d/%m/%Y").date()
                        except ValueError:
                            current_entry_date = fields.Date.today()

                # Convertir cuenta a 6 dígitos
                six_digit_account, partner_id = self._convert_account_to_six_digits(account_code, title)
                if partner_id:
                    partners_created += 1

                # Añadir línea al asiento actual
                current_entry_lines.append({
                    'account_code': six_digit_account,
                    'name': title or concept,
                    'debit': debit,
                    'credit': credit,
                    'ref': concept,
                    'partner_id': partner_id,
                })

            except Exception as e:
                _logger.error(f"Error procesando fila {row_idx+1}: {str(e)}")
                continue

        # Crear el último asiento si queda alguno pendiente
        if current_entry_number and current_entry_lines:
            self._create_excel_accounting_entry(
                current_entry_date,
                current_entry_number,
                current_entry_lines
            )
            entries_created += 1

        return {
            'entries_created': entries_created,
            'partners_created': partners_created
        }

    def _convert_account_to_six_digits(self, account_code, partner_name):
        """
        Convierte una cuenta de 8 dígitos a 6 dígitos.
        Para cuentas que empiezan por 400, 410 o 430, crea un partner si no existe.
        """
        partner_id = False
        account_obj = self.env['account.account']

        # Asegurar que tenemos una cadena
        account_code = str(account_code)

        # Si la cuenta tiene 8 dígitos, convertir a 6 tomando los 3 primeros y los 3 últimos
        if len(account_code) == 8:
            six_digit_code = account_code[:3] + account_code[5:]
        else:
            six_digit_code = account_code

        # Si la cuenta comienza con 400, 410 o 430
        if account_code.startswith(('400', '410', '430')) and partner_name:
            # Convertir a formato XXX000
            generic_code = account_code[:3] + '000'

            # Buscar si existe cuenta con ese código genérico
            generic_account = account_obj.search([('code', '=', generic_code)], limit=1)

            # Si no existe la cuenta genérica, crearla
            if not generic_account:
                account_type = self._determine_account_type(generic_code)
                generic_account = account_obj.create({
                    'code': generic_code,
                    'name': f"Cuenta genérica {generic_code}",
                    'account_type': account_type,
                })

            # Crear o buscar el partner
            partner = self.env['res.partner'].search([('name', '=ilike', partner_name)], limit=1)
            if not partner and partner_name and len(partner_name) > 1:
                partner = self.env['res.partner'].create({
                    'name': partner_name,
                    'ref': account_code,
                    'is_company': True,
                })
            partner_id = partner.id if partner else False

            # Devolver el código genérico
            return generic_code, partner_id

        # Buscar si la cuenta de 6 dígitos existe
        six_digit_account = account_obj.search([('code', '=', six_digit_code)], limit=1)

        # Si no existe, crearla
        if not six_digit_account:
            account_type = self._determine_account_type(six_digit_code)
            six_digit_account = account_obj.create({
                'code': six_digit_code,
                'name': partner_name or f"Cuenta {six_digit_code}",
                'account_type': account_type,
            })

        return six_digit_code, partner_id

    def _create_excel_accounting_entry(self, date, number, lines):
        """Crea un asiento contable con sus líneas desde Excel."""
        account_move_obj = self.env['account.move']
        account_account_obj = self.env['account.account']

        # Valores para el asiento contable
        move_vals = {
            'date': date,
            'ref': f"Asiento {number}",
            'journal_id': self.journal_id.id,
            'line_ids': [],
        }

        # Preparar líneas del asiento
        for line in lines:
            # Buscar la cuenta contable
            account = account_account_obj.search([('code', '=', line['account_code'])], limit=1)
            if not account:
                continue

            # Añadir línea al asiento
            move_vals['line_ids'].append((0, 0, {
                'name': line['name'] or '/',
                'account_id': account.id,
                'partner_id': line['partner_id'] if line.get('partner_id') else False,
                'debit': line['debit'],
                'credit': line['credit'],
                'ref': line['ref'],
            }))

        print("*"*80)
        print("move_vals", move_vals)

        # Crear el asiento si hay líneas
        if move_vals['line_ids']:
            account_move_obj.create(move_vals)

    def _determine_account_type(self, code):
        """
        Determina el tipo de cuenta según su código.
        """
        # Primeros dígitos del código de cuenta
        prefix = code[:1]

        # Mapeo de prefijos a tipos de cuenta para Odoo 17
        type_mapping = {
            '1': 'equity',  # Cuentas de capital
            '2': 'asset_non_current',  # Activo no corriente
            '3': 'asset_current',  # Existencias
            '4': 'liability_current',  # Pasivo
            '5': 'liability_current',  # Cuentas financieras
            '6': 'expense',  # Gastos
            '7': 'income',  # Ingresos
        }
        return type_mapping.get(prefix, 'asset_current')
