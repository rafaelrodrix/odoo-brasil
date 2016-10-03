# -*- coding: utf-8 -*-
# © 2014  Renato Lima - Akretion
# © 2013  Raphaël Valyi - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        super(SaleOrder, self)._amount_all()
        for order in self:
            order.update({
                'amount_total': order.amount_total + order.total_frete + order.total_seguro + order.total_despesas,
            })

    def _calc_ratio(self, qty, total):
        if total > 0:
            return qty / total
        else:
            return 0

    @api.onchange('total_despesas', 'total_seguro', 'total_frete')
    def _onchange_despesas_frete_seguro(self):
        for l in self.order_line:
            item_liquido = l.valor_bruto - l.valor_desconto
            total_liquido = self.total_bruto - self.total_desconto
            percentual = self._calc_ratio(item_liquido, total_liquido)
            l.update({
                'valor_seguro': self.total_seguro * percentual,
                'valor_frete': self.total_frete * percentual,
                'outras_despesas': self.total_despesas * percentual
            })

    total_despesas = fields.Float(
        string='Outras Despesas', default=0.00,
        digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)]})
    total_seguro = fields.Float(
        string='Seguro', default=0.00, digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)]})
    total_frete = fields.Float(
        string='Frete', default=0.00, digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)]})


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id',
                 'valor_seguro', 'valor_frete', 'outras_despesas')
    def _compute_amount(self):
        super(SaleOrderLine, self)._compute_amount()
        for item in self:
            somar = item.valor_seguro + item.valor_frete + item.outras_despesas
            item.update({
                'price_total': item.price_total + somar,
            })

    valor_seguro = fields.Float(
        'Seguro', default=0.0,
        digits=dp.get_precision('Account'), readonly=True)
    outras_despesas = fields.Float(
        'Despesas', default=0.0,
        digits=dp.get_precision('Account'), readonly=True)
    valor_frete = fields.Float(
        'Frete', default=0.0,
        digits=dp.get_precision('Account'), readonly=True)

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        res['valor_seguro'] = self.valor_seguro
        res['outras_despesas'] = self.outras_despesas
        res['valor_frete'] = self.valor_frete
        return res
