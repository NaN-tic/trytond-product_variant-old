#-*- coding:utf-8 -*-
#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import copy
import itertools

from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Equal, Eval, Greater, Not, In, If, Get, Bool, Or, And
from trytond.transaction import Transaction

class Product(ModelSQL, ModelView):
    _name = 'product.product'

    identifier = fields.Char('Identifier', readonly=True)

    def __init__(self):
        super(Product, self).__init__()
        fields = self._columns
        for field in self._inherit_fields.itervalues():
            if not field in fields:
                field[2].states['readonly'] = Eval('variant')
        self.template = copy.copy(self.template)
        self.template.states = copy.copy(self.template.states)
        self.template.states['required'] = Greater(Eval('active_id', 0), 0)
        self.template.states['invisible'] = Not(Greater(Eval('active_id', 0), 0))
        self._reset_columns()

    def fields_get(self, fields_names=None):
        res = super(Product, self).fields_get(fields_names)
        if 'codebase' in res.keys(): del res['codebase']
        return res

    def create(self, vals):
        if not vals.get('template'):
            vals.pop('template')
        return super(Product, self).create(vals)

    def delete(self, ids):
        if isinstance(ids, (int, long)):
            ids = [ids]
        Transaction().set_context(save_templates=True)
        res = super(Product, self).delete(ids)
        return res

Product()

class Template(ModelSQL, ModelView):
    _name = "product.template"

    codebase = fields.Char('Code')
    attributes = fields.Many2Many('product.template-product.attribute',
                                  'template', 'attribute', 'Attributes')

    variant = fields.Function(fields.Boolean('Variant'),
            'get_variants')

    description = fields.Text("Description", translate=True)

    def __init__(self):
        super(Template, self).__init__()
        self._rpc.update({
            'generate_contained_products': True,
                   })

    def delete(self, ids):
        if isinstance(ids, (int, long)):
            ids = [ids]
        templates = self.browse(ids)
        for template in templates:
            if template.products or Transaction().context.get('save_templates'):
                return
        res = super(Template, self).delete(ids)
        return res

    def get_variants(self, ids, name):
        res = {}
        for template in self.browse(ids):
            res[template.id] = False
            if len(template.products) > 1:
                res[template.id] = True
        return res

    def generate_contained_products(self, ids):
        """
        generate all variants - if not already done
        """
        product_obj = self.pool.get('product.product')
        config_obj = self.pool.get('product.variant.configuration')
        config = config_obj.browse(1)
        if not ids:
            return {}
        res = {}
        for template in self.browse(ids):
            if not template.attributes:
                continue
            already = [p.code for p in template.products]
            #map?
            identifier = [(i.sequence, i.values) for i in template.attributes]
            identifier.sort()
            identifier = [i[1] for i in identifier]
            variants = list(itertools.product(*identifier))

            for variant in variants:
                sep = config.identifier_seperator or ''
                identifier = sep.join([i.name for i in variant])
                code = '%s%s' % (template.codebase or '',
                                 config.code_seperator or '')
                sep = config.code_seperator or ''
                code = code + sep.join([i.code for i in variant])
                if not code in already:
                    product_obj.create({'template':template.id,
                                        'identifier':identifier,
                                        'code':code})
        return res
Template()

class ProductAttribute(ModelSQL, ModelView):
    "Possible Attribute"
    _name = "product.attribute"
    _description = __doc__

    sequence = fields.Integer('Sequence')
    name = fields.Char('Name', size=None, required=True, translate=True,
            select=1)
    values = fields.One2Many('product.attribute.value', 'attribute', 'Values')

    def __init__(self):
        super(ProductAttribute, self).__init__()

ProductAttribute()


class ProductAttributeValue(ModelSQL, ModelView):
    "Values for Attributes"
    _name = "product.attribute.value"
    _description = __doc__

    sequence = fields.Integer('Sequence')
    name = fields.Char('Name', required=True, select=1)
    code = fields.Char('Code', required=True)
    attribute = fields.Many2One('product.attribute', 'Product Attribute',
            required=True, ondelete='CASCADE', select=1)
    def __init__(self):
        super(ProductAttributeValue, self).__init__()
        self._order.insert(0, ('sequence', 'ASC'))

ProductAttributeValue()


class ProductTemplateAttribute(ModelSQL, ModelView):
    "Product Template Product Attribute"
    _name = "product.template-product.attribute"
    _description = __doc__


    attribute = fields.Many2One('product.attribute', 'Product Attribute',
            ondelete='CASCADE', select=1, required=True)
    template = fields.Many2One('product.template', 'Product template',
            ondelete='CASCADE', select=1, required=True)

ProductTemplateAttribute()



