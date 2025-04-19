from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    registration_date = fields.Date(
        string="Registration Date",
        default=fields.Date.context_today,
        help="Date when this partner was registered."
    )
    membership_plan = fields.Selection([
        ('annual', 'Annual'),
        ('biannual', 'Biannual')
    ],
        string="Membership Plan",
        help="Type of membership plan",
    )
