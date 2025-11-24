# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Club Talento Account Import",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "summary": "Importar asientos contables desde Excel con normalización de cuentas y terceros",
    "author": "Xtendoo",
    "website": "https://github.com/xtendoo-corporation/custom-club-talento",
    "license": "AGPL-3",
    "depends": [
        "account",
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/club_talento_import_wizard_views.xml",
        "views/club_talento_import_menu.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}

