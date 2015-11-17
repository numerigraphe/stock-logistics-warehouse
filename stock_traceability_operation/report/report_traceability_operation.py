# -*- coding: utf-8 -*-
# © 2015 Numérigraphe
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import tools, models, fields, api
from openerp.addons import decimal_precision as dp


class ReportStockTraceabilityOperation(models.Model):
    _name = 'report.stock.traceability_operation'
    _description = "Traceability"
    _order = 'date, move_id, operation_link_id'
    _auto = False

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute(
            """
            CREATE OR REPLACE VIEW """ + self._table + """ (
                id,
                name,
                move_id,
                operation_link_id,
                picking_id,
                origin,
                picking_type_id,
                create_date,
                product_id,
                product_uom,
                product_uos_qty,
                product_uos,
                location_id,
                location_dest_id,
                "date",
                date_expected,
                state,
                partner_id)
            AS (
                SELECT
                    COALESCE(link.id, -move.id),
                    move.name,
                    move.id,
                    link.id,
                    move.picking_id,
                    move.origin,
                    move.picking_type_id,
                    move.create_date,
                    move.product_id,
                    template.uom_id,
                    move.product_uos_qty,
                    move.product_uos,
                    COALESCE(operation.location_id, move.location_id),
                    COALESCE(operation.location_dest_id,
                             move.location_dest_id),
                    move."date",
                    move.date_expected,
                    move.state,
                    move.partner_id
                FROM
                    stock_move AS move
                    INNER JOIN product_product AS product
                        ON product.id = move.product_id
                    INNER JOIN product_template AS template
                        ON template.id = product.product_tmpl_id
                    LEFT JOIN (
                        stock_move_operation_link AS link
                        INNER JOIN stock_pack_operation AS operation
                            ON operation.id = link.operation_id)
                    ON link.move_id = move.id)
            """)

    move_id = fields.Many2one(
        'stock.move', 'Stock Move',
        help="The stock move on which this part of the traceability is based")
    operation_link_id = fields.Many2one(
        'stock.move.operation.link', 'Pack Operation Link',
        help="The link to a pack operation on which this part of the "
             "traceability is based. When this field is empty, this part of "
             "the traceability is directly based on the Stock Move.")
    #  Same fields as Stock Moves, to be able to reuse the standard view
    name = fields.Char('Move description')
    picking_id = fields.Many2one('stock.picking', 'Reference')
    origin = fields.Char('Source')
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type')
    create_date = fields.Datetime('Creation Date')
    product_id = fields.Many2one('product.product', 'Product')
    product_uom_qty = fields.Float(
        'Quantity',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        compute='_get_product_uom_qty', store=False,
        help="This is the quantity of products moved in this Stock Move or "
             "in this Pack Operation")
    product_uom = fields.Many2one(
        'product.uom', 'Unit of Measure',
        help="The unit of measure of the product")
    product_uos_qty = fields.Float(
        'Quantity (UOS)',
        digits_compute=dp.get_precision('Product Unit of Measure'))
    product_uos = fields.Many2one('product.uom', 'Product UOS')
    location_id = fields.Many2one('stock.location', 'Source Location')
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location')
    date = fields.Datetime('Date')
    date_expected = fields.Datetime('Expected Date')
    state = fields.Selection(
        [('draft', 'New'),
         ('cancel', 'Cancelled'),
         ('waiting', 'Waiting Another Move'),
         ('confirmed', 'Waiting Availability'),
         ('assigned', 'Available'),
         ('done', 'Done')],
        'Status')
    partner_id = fields.Many2one('res.partner', 'Destination Address')

    @api.multi
    @api.depends('move_id.product_uom_qty', 'operation_link_id.qty')
    def _get_product_uom_qty(self):
        """Get the move's qty in product UoM when no operation involved

        If the line is based on a pack operation, the quantity is that of
        the operation/move link, which is in the product's main UoM already.

        On the other hand, the stock move's quantity is store in a user-chosen
        UoM in the database, and the standard provides a computed field to get
        this quantity in the product's main UoM.
        So if the line is base on a stock move, we use product_qty of making
        the conversion in SQL to avoid rounding errors."""
        for line in self:
            line.product_uom_qty = (line.operation_link_id.qty or
                                    line.move_id.product_qty)
