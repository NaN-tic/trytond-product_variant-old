#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import copy
import itertools
from trytond.pool import Pool
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Greater, Or, And, Not, Bool, PYSONEncoder
from trytond.transaction import Transaction

class Product(ModelSQL, ModelView):
    _name = 'product.product'

    attribute_values = fields.Many2Many('product.product-attribute.value',
        'product', 'value', 'Values', readonly=True)
    template = fields.Many2One('product.template', 'Product Template',
        ondelete='CASCADE', select=1,
        states={
            'required':Greater(Eval('active_id', 0), 0),
            'invisible':Not(Greater(Eval('active_id', 0), 0)),
            'readonly':Not(Bool(Eval('variant')))
        })

    def create(self, values):
        if not values.get('template'):
            values = values.copy()
            try:values.pop('template')
            except:pass
        return super(Product, self).create(values)

    def delete(self, ids):
        if isinstance(ids, (int, long)):
            ids = [ids]
        Transaction().set_context(save_templates=True)
        res = super(Product, self).delete(ids)
        return res

Product()


class Template(ModelSQL, ModelView):
    _name = "product.template"

    basecode = fields.Char('Basecode',
        states={
            'invisible': Not(Bool(Eval('attributes')))
        }, depends=['attributes'])
    attributes = fields.Many2Many('product.template-product.attribute',
        'template', 'attribute', 'Attributes')
    variant = fields.Function(fields.Boolean('Variant', select=1),
        'get_variants', searcher="search_variant")
    basedescription = fields.Text("Basedescription", translate=True)

    def __init__(self):
        super(Template, self).__init__()
        self._rpc.update({
            'generate_variants': True,
        })

        self._buttons.update({
                'generate_variants': {
                    'invisible':Eval('template'),
                    }
            })

        for column in self._columns.itervalues():
            already = False
            if 'readonly' in column.states:
                already = column.states['readonly']
            column.states = {'readonly': Or(And(Bool(Eval('template')),
                Bool(Eval('variant'))), already)}

    def delete(self, ids):
        if isinstance(ids, (int, long)):
            ids = [ids]
        templates = self.browse(ids)
        for template in templates:
            if template.products or \
            Transaction().context.get('save_templates'):
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

    def search_variant(self, name, clause):
        res = []
        ids = self.search([('id', '>', 0)])
        records = self.browse(ids)
        if clause[2] == True:
            for template in records:
                if len(template.products) > 1:
                    res.append(template.id)
        else:
            for template in records:
                if len(template.products) == 1:
                    res.append(template.id)
        return [('id', 'in', res)]

    def create_code(self, basecode, variant):
        config_obj = Pool().get('product.variant.configuration')
        config = config_obj.browse(1)
        sep = config.code_separator or ''
        code = '%s%s' % (basecode or '', ['', sep][bool(basecode)])
        code = code + sep.join(i.code for i in variant)
        return code

    def create_product(self, template, variant):
        "create the product"
        pool = Pool()
        product_obj = pool.get('product.product')
        value_obj = pool.get('product.product-attribute.value')
        code = self.create_code(template.basecode, variant)
        new_id = product_obj.create({'template':template.id,
            'code':code})
        for value in variant:
            value_obj.create({'product':new_id, 'value':value.id})
        return True

    @ModelView.button
    def generate_variants(self, ids):
        """generate variants"""
        if not ids:
            return False
        for template in self.browse(ids):
            if not template.attributes:
                continue
            already = set(tuple(p.attribute_values) for p in template.products)
            values = [i.values for i in template.attributes]
            variants = itertools.product(*values)
            for variant in variants:
                if not variant in already:
                    self.create_product(template, variant)
        return True

Template()


class ProductAttribute(ModelSQL, ModelView):
    "Product Attribute"
    _name = "product.attribute"
    _description = __doc__

    sequence = fields.Integer('Sequence')
    name = fields.Char('Name', required=True, translate=True, select=1,
                       order_field="%(table)s.sequence %(order)s")
    values = fields.One2Many('product.attribute.value', 'attribute', 'Values')

    def __init__(self):
        super(ProductAttribute, self).__init__()
        self._order.insert(0, ('sequence', 'ASC'))

ProductAttribute()


class AttributeValue(ModelSQL, ModelView):
    "Values for Attributes"
    _name = "product.attribute.value"
    _description = __doc__

    sequence = fields.Integer('Sequence')
    name = fields.Char('Name', required=True, select=1)
    code = fields.Char('Code', required=True)
    attribute = fields.Many2One('product.attribute', 'Product Attribute',
        required=True)

    def __init__(self):
        super(AttributeValue, self).__init__()
        self._order.insert(0, ('sequence', 'ASC'))

AttributeValue()


class ProductTemplateAttribute(ModelSQL, ModelView):
    "Product Template - Product Attribute"
    _name = "product.template-product.attribute"
    _description = __doc__

    attribute = fields.Many2One('product.attribute', 'Product Attribute',
            ondelete='RESTRICT', required=True)
    template = fields.Many2One('product.template', 'Product template',
            ondelete='CASCADE', required=True)

ProductTemplateAttribute()


class ProductAttributeValue(ModelSQL, ModelView):
    "Product - Product Attribute Value"
    _name = "product.product-attribute.value"
    _description = __doc__

    product = fields.Many2One('product.product', 'Product',
            ondelete='CASCADE', required=True)
    value = fields.Many2One('product.attribute.value', 'Attribute Value',
            ondelete='CASCADE', required=True)

ProductAttributeValue()
