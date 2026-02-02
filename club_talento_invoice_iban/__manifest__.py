# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Club Talento - IBAN en Factura PDF",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "summary": "Imprime el IBAN del cliente en facturas según métodos de pago configurados",
    "author": "Xtendoo",
    "website": "https://github.com/xtendoo-corporation/custom-club-talento",
    "license": "AGPL-3",
    "depends": [
        "account",
    ],
    "data": [
        "views/res_config_settings_views.xml",
        "views/account_move_views.xml",
        "views/report_invoice_document.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
