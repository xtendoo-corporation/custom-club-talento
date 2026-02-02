# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    invoice_iban_payment_method_line_ids = fields.Many2many(
        comodel_name="account.payment.method.line",
        relation="company_invoice_iban_pay_method_line_rel",
        column1="company_id",
        column2="payment_method_line_id",
        string="Métodos de pago para mostrar IBAN",
        domain="[('company_id', '=', id)]",
        help="Seleccione los métodos de pago para los cuales se debe mostrar "
        "el IBAN del cliente en el PDF de la factura.",
    )
