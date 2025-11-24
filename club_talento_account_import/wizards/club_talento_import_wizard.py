# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io
import logging
import locale
from datetime import datetime
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

try:
    import openpyxl
except ImportError:
    openpyxl = None

from ..models.account_normalizer import (
    normalize_account,
    infer_account_type,
    is_partner_account,
)

_logger = logging.getLogger(__name__)


class ClubTalentoImportWizard(models.TransientModel):
    _name = "club.talento.import.wizard"
    _description = "Asistente de importación de asientos Club Talento"

    # Campos de entrada
    file_data = fields.Binary(
        string="Archivo Excel",
        required=True,
        help="Archivo .xlsx con hojas 2023, 2024, 2025"
    )
    file_name = fields.Char(string="Nombre del archivo")

    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company
    )

    journal_id = fields.Many2one(
        "account.journal",
        string="Diario",
        required=True,
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        help="Diario donde se crearán los asientos"
    )

    create_accounts = fields.Boolean(
        string="Crear cuentas si no existen",
        default=True,
        help="Si está marcado, crea automáticamente las cuentas que no existan"
    )

    create_partners = fields.Boolean(
        string="Crear contactos si no existen",
        default=True,
        help="Si está marcado, crea automáticamente los contactos que no existan"
    )

    post_balanced = fields.Boolean(
        string="Publicar asientos que cuadren",
        default=False,
        help="Publica automáticamente los asientos cuyo balance sea cero"
    )

    # Campos de resultado
    result_text = fields.Text(
        string="Resultado",
        readonly=True,
        help="Resumen de la importación"
    )

    state = fields.Selection(
        [("draft", "Borrador"), ("done", "Completado")],
        default="draft",
        string="Estado"
    )

    move_ids = fields.Many2many(
        "account.move",
        string="Asientos creados",
        readonly=True
    )

    @api.onchange("company_id")
    def _onchange_company_id(self):
        """Actualiza el dominio del diario cuando cambia la compañía."""
        if self.company_id:
            # Buscar diario de operaciones diversas
            journal = self.env["account.journal"].search([
                ("type", "=", "general"),
                ("company_id", "=", self.company_id.id),
            ], limit=1)
            if journal:
                self.journal_id = journal

    def action_import(self):
        """Ejecuta la importación del archivo Excel."""
        self.ensure_one()

        if not openpyxl:
            raise UserError(_(
                "El módulo 'openpyxl' no está instalado. "
                "Por favor, instálelo con: pip install openpyxl"
            ))

        if not self.file_data:
            raise UserError(_("Debe cargar un archivo Excel."))

        # Decodificar archivo
        file_content = base64.b64decode(self.file_data)
        workbook = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)

        # Validar hojas requeridas
        required_sheets = ["2023", "2024", "2025"]
        missing_sheets = [s for s in required_sheets if s not in workbook.sheetnames]
        if missing_sheets:
            raise UserError(_(
                "Faltan las siguientes hojas en el archivo: %s"
            ) % ", ".join(missing_sheets))

        # Estadísticas
        stats = {
            "moves_created": 0,
            "moves_draft": 0,
            "moves_posted": 0,
            "partners_created": 0,
            "accounts_created": 0,
            "warnings": [],
        }

        all_moves = self.env["account.move"]

        # Procesar cada hoja
        for sheet_name in required_sheets:
            year = int(sheet_name)
            sheet = workbook[sheet_name]

            _logger.info("Procesando hoja %s...", sheet_name)

            # Parsear datos
            lines_data = self._parse_sheet(sheet, year, stats)

            # Agrupar por (Año, Asto., Fecha)
            grouped = self._group_lines(lines_data)

            # Crear asientos
            moves = self._create_moves(grouped, stats)
            all_moves |= moves

        # Guardar resultados
        self.move_ids = [(6, 0, all_moves.ids)]
        self.state = "done"
        self.result_text = self._format_results(stats)

        # Retornar acción para ver asientos creados
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")
        action.update({
            "name": _("Asientos importados"),
            "domain": [("id", "in", all_moves.ids)],
            "context": {"create": False},
        })
        return action

    def _parse_sheet(self, sheet, year, stats):
        """
        Parsea una hoja de Excel y extrae las líneas de datos.

        Returns:
            list: Lista de diccionarios con los datos de cada línea
        """
        lines_data = []

        # Buscar fila de encabezados
        header_row = None
        for idx, row in enumerate(sheet.iter_rows(min_row=1, max_row=20), start=1):
            values = [str(cell.value).strip().lower() if cell.value else "" for cell in row]
            if "cuenta" in values and "debe" in values and "haber" in values:
                header_row = idx
                # Mapear columnas
                col_map = {}
                for col_idx, val in enumerate(values):
                    if "fecha" in val:
                        col_map["fecha"] = col_idx
                    elif "asto" in val:
                        col_map["asto"] = col_idx
                    elif "ord" in val:
                        col_map["ord"] = col_idx
                    elif "dia" in val:
                        col_map["dia"] = col_idx
                    elif "cuenta" in val:
                        col_map["cuenta"] = col_idx
                    elif "titulo" in val or "título" in val:
                        col_map["titulo"] = col_idx
                    elif "concepto" in val:
                        col_map["concepto"] = col_idx
                    elif "debe" in val:
                        col_map["debe"] = col_idx
                    elif "haber" in val:
                        col_map["haber"] = col_idx
                break

        if not header_row:
            stats["warnings"].append(f"No se encontró fila de encabezados en hoja {year}")
            return lines_data

        # Procesar filas de datos
        for row in sheet.iter_rows(min_row=header_row + 1):
            # Verificar si la fila está vacía
            if all(cell.value is None or str(cell.value).strip() == "" for cell in row):
                continue

            # Extraer valores
            try:
                fecha_raw = row[col_map.get("fecha", 0)].value if "fecha" in col_map else None
                asto = row[col_map.get("asto", 1)].value if "asto" in col_map else None
                cuenta_raw = row[col_map.get("cuenta", 4)].value if "cuenta" in col_map else None
                titulo = row[col_map.get("titulo", 5)].value if "titulo" in col_map else ""
                concepto = row[col_map.get("concepto", 6)].value if "concepto" in col_map else ""
                debe = row[col_map.get("debe", 7)].value if "debe" in col_map else 0
                haber = row[col_map.get("haber", 8)].value if "haber" in col_map else 0

                # Validar datos mínimos
                if not cuenta_raw:
                    continue

                # Normalizar valores
                if not asto:
                    asto = "0"
                asto = str(asto).strip()

                titulo = str(titulo).strip() if titulo else ""
                concepto = str(concepto).strip() if concepto else ""

                # Convertir importes (manejar NaN)
                try:
                    debe = float(debe) if debe not in (None, "", "None") else 0.0
                except (ValueError, TypeError):
                    debe = 0.0

                try:
                    haber = float(haber) if haber not in (None, "", "None") else 0.0
                except (ValueError, TypeError):
                    haber = 0.0

                # Si ambos son 0, saltar
                if debe == 0 and haber == 0:
                    continue

                # Parsear fecha
                fecha = self._parse_date(fecha_raw, year, stats)

                lines_data.append({
                    "fecha": fecha,
                    "asto": asto,
                    "cuenta_raw": str(cuenta_raw),
                    "titulo": titulo,
                    "concepto": concepto,
                    "debe": debe,
                    "haber": haber,
                    "year": year,
                })

            except Exception as e:
                _logger.warning("Error procesando fila: %s", e)
                continue

        _logger.info("Parseadas %d líneas de la hoja %s", len(lines_data), year)
        return lines_data

    def _parse_date(self, fecha_raw, year, stats):
        """
        Parsea la fecha en formato '01-Oct.' y asigna el año.

        Args:
            fecha_raw: Valor de la celda de fecha
            year: Año de la hoja
            stats: Diccionario de estadísticas

        Returns:
            datetime.date: Fecha parseada
        """
        if not fecha_raw:
            stats["warnings"].append(f"Fecha vacía, usando 01/01/{year}")
            return datetime(year, 1, 1).date()

        fecha_str = str(fecha_raw).strip()

        # Intentar varios formatos
        formats_to_try = [
            ("%d-%b.", "es_ES.UTF-8"),  # 01-Oct.
            ("%d-%b", "es_ES.UTF-8"),   # 01-Oct
            ("%d/%m/%Y", None),         # 01/10/2023
            ("%d/%m/%y", None),         # 01/10/23
            ("%Y-%m-%d", None),         # 2023-10-01
        ]

        for fmt, loc in formats_to_try:
            try:
                if loc:
                    # Intentar configurar locale español
                    try:
                        locale.setlocale(locale.LC_TIME, loc)
                    except:
                        pass

                parsed = datetime.strptime(fecha_str, fmt)
                # Sobrescribir año
                return parsed.replace(year=year).date()
            except ValueError:
                continue

        # Si es datetime directamente
        if isinstance(fecha_raw, datetime):
            return fecha_raw.replace(year=year).date()

        # Fallback: primer día del año
        stats["warnings"].append(
            f"No se pudo parsear fecha '{fecha_str}', usando 01/01/{year}"
        )
        return datetime(year, 1, 1).date()

    def _group_lines(self, lines_data):
        """
        Agrupa líneas por (Año, Asto., Fecha).

        Returns:
            dict: {(year, asto, fecha): [líneas]}
        """
        grouped = defaultdict(list)

        for line in lines_data:
            key = (line["year"], line["asto"], line["fecha"])
            grouped[key].append(line)

        return grouped

    def _create_moves(self, grouped, stats):
        """
        Crea los asientos contables a partir de las líneas agrupadas.

        Returns:
            recordset: account.move creados
        """
        moves = self.env["account.move"]

        for (year, asto, fecha), lines in grouped.items():
            try:
                move = self._create_single_move(year, asto, fecha, lines, stats)
                if move:
                    moves |= move
                    stats["moves_created"] += 1
            except Exception as e:
                msg = f"Error creando asiento {asto} ({year}): {e}"
                _logger.error(msg)
                stats["warnings"].append(msg)

        return moves

    def _create_single_move(self, year, asto, fecha, lines, stats):
        """
        Crea un único asiento contable.

        Returns:
            account.move: Asiento creado o False si hay error
        """
        # Preparar líneas
        move_lines = []
        balance_total = 0.0
        missing_accounts = set()

        for line in lines:
            # Normalizar cuenta
            code6 = normalize_account(line["cuenta_raw"])
            if not code6:
                stats["warnings"].append(
                    f"Cuenta inválida '{line['cuenta_raw']}' en asiento {asto}"
                )
                continue

            # Buscar o crear cuenta
            account = self._get_or_create_account(
                code6, line["titulo"] or line["concepto"], stats
            )
            if not account:
                missing_accounts.add(code6)
                continue

            # Buscar o crear partner si es cuenta de tercero
            partner_id = False
            if is_partner_account(code6):
                partner_name = line["titulo"] or line["concepto"]
                if partner_name:
                    partner = self._get_or_create_partner(partner_name, stats)
                    if partner:
                        partner_id = partner.id

            # Calcular balance
            balance = line["debe"] - line["haber"]
            balance_total += balance

            # Preparar valores de línea
            line_vals = {
                "account_id": account.id,
                "name": line["concepto"] or line["titulo"] or "/",
                "debit": line["debe"],
                "credit": line["haber"],
            }

            if partner_id:
                line_vals["partner_id"] = partner_id

            move_lines.append((0, 0, line_vals))

        # Si faltan cuentas y no se crean automáticamente, abortar
        if missing_accounts:
            raise ValidationError(_(
                "Faltan las siguientes cuentas y la opción "
                "'Crear cuentas si no existen' está desactivada: %s"
            ) % ", ".join(sorted(missing_accounts)))

        if not move_lines:
            return False

        # Crear asiento (la compañía se hereda del diario seleccionado)
        move_vals = {
            "journal_id": self.journal_id.id,
            "date": fecha,
            "ref": f"Importado - Año {year} - Asto. {asto}",
            "line_ids": move_lines,
        }

        move = self.env["account.move"].with_company(self.company_id).create(move_vals)

        # Verificar balance y decidir si publicar
        tolerance = 0.01
        is_balanced = abs(balance_total) < tolerance

        if is_balanced and self.post_balanced:
            try:
                move.action_post()
                stats["moves_posted"] += 1
            except Exception as e:
                msg = f"No se pudo publicar asiento {asto} ({year}): {e}"
                _logger.warning(msg)
                stats["warnings"].append(msg)
                stats["moves_draft"] += 1
        else:
            stats["moves_draft"] += 1
            if not is_balanced:
                msg = (
                    f"Asiento {asto} ({year}) no cuadra. "
                    f"Diferencia: {balance_total:.2f}. Dejado en borrador."
                )
                move.message_post(body=msg)
                stats["warnings"].append(msg)

        # Mensaje en chatter
        summary = (
            f"Asiento importado:\n"
            f"- Año: {year}\n"
            f"- Asto. legacy: {asto}\n"
            f"- Fecha: {fecha}\n"
            f"- Líneas: {len(lines)}\n"
            f"- Balance: {balance_total:.2f}\n"
        )
        move.message_post(body=summary)

        return move

    def _get_or_create_account(self, code6, name, stats):
        """
        Busca o crea una cuenta contable.

        Args:
            code6: Código normalizado de 6 dígitos
            name: Nombre de la cuenta
            stats: Estadísticas

        Returns:
            account.account o False
        """
        # Buscar cuenta existente con el contexto de la compañía
        account = self.env["account.account"].with_company(self.company_id).search([
            ("code", "=", code6),
        ], limit=1)

        if account:
            return account

        # Si no existe y no se debe crear, retornar False
        if not self.create_accounts:
            return False

        # Crear cuenta
        account_type = infer_account_type(code6)

        account = self.env["account.account"].with_company(self.company_id).create({
            "code": code6,
            "name": name or f"Cuenta {code6}",
            "account_type": account_type,
        })

        stats["accounts_created"] += 1
        _logger.info("Cuenta creada: %s - %s", code6, name)

        return account

    def _get_or_create_partner(self, name, stats):
        """
        Busca o crea un partner.

        Args:
            name: Nombre del partner
            stats: Estadísticas

        Returns:
            res.partner o False
        """
        if not name:
            return False

        # Buscar partner existente (case-insensitive)
        partner = self.env["res.partner"].search([
            ("name", "=ilike", name.strip()),
        ], limit=1)

        if partner:
            return partner

        # Si no existe y no se debe crear, retornar False
        if not self.create_partners:
            return False

        # Crear partner
        partner = self.env["res.partner"].create({
            "name": name.strip(),
            "company_type": "company",
        })

        stats["partners_created"] += 1
        _logger.info("Partner creado: %s", name)

        return partner

    def _format_results(self, stats):
        """Formatea el resumen de resultados."""
        lines = [
            "=" * 60,
            "RESUMEN DE IMPORTACIÓN",
            "=" * 60,
            "",
            f"✓ Asientos creados: {stats['moves_created']}",
            f"  - Publicados: {stats['moves_posted']}",
            f"  - En borrador: {stats['moves_draft']}",
            "",
            f"✓ Partners creados: {stats['partners_created']}",
            f"✓ Cuentas creadas: {stats['accounts_created']}",
            "",
        ]

        if stats["warnings"]:
            lines.append("⚠ ADVERTENCIAS:")
            lines.append("")
            for idx, warning in enumerate(stats["warnings"][:10], 1):
                lines.append(f"  {idx}. {warning}")

            if len(stats["warnings"]) > 10:
                lines.append(f"  ... y {len(stats['warnings']) - 10} más")

        return "\n".join(lines)

