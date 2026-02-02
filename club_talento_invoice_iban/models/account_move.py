# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    print_customer_iban = fields.Boolean(
        string='Imprimir IBAN del cliente',
        compute='_compute_print_customer_iban',
        store=True,
        help='Si está activo, se imprimirá el IBAN del cliente en el PDF de la factura.',
    )

    @api.depends('preferred_payment_method_line_id')
    def _compute_print_customer_iban(self):
        for move in self:
            print_iban = False
            if move.preferred_payment_method_line_id:
                configured_methods = move.company_id.invoice_iban_payment_method_line_ids
                if move.preferred_payment_method_line_id.id in configured_methods.ids:
                    print_iban = True

            move.print_customer_iban = print_iban


