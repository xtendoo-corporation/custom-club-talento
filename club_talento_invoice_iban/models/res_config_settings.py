# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    invoice_iban_payment_method_line_ids = fields.Many2many(
        related="company_id.invoice_iban_payment_method_line_ids",
        readonly=False,
        domain="[('company_id', '=', company_id)]",
    )
