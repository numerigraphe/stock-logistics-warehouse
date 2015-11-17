# -*- coding: utf-8 -*-
# © 2015 Numérigraphe
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models
from openerp.tools.translate import _


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.multi
    def action_view_quant_history(self):
        '''Replace the action on stock moves into an action on the report

        We are **not calling super()**, on purpose: changing the domain string
        is too complex for the gain it brings.
        '''
        move_ids = self.mapped('history_ids').ids
        if not move_ids:
            return False
        return {
            'domain': "[('move_id', 'in', "
                      "  [" + ','.join(map(str, move_ids)) + "])]",
            'name': _('Traceability'),
            'view_mode': 'tree',
            'view_type': 'form',
            'res_model': 'report.stock.traceability_operation',
            'type': 'ir.actions.act_window',
            'context': {'search_default_done': True}}
