# -*- coding: utf-8 -*-
# © 2015 Numérigraphe
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    @api.multi
    def action_traceability(self):
        '''Replace the action on stock moves into an action on the report

        We are **not calling super()**, on purpose: changing the domain string
        is too complex for the gain it brings.'''
        quants = self.env['stock.quant'].search([('lot_id', 'in', self.ids)])
        return quants.action_view_quant_history()
