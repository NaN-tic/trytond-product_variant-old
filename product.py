#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import copy
import itertools

from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Greater, Or, And, Not, Bool, PYSONEncoder
from trytond.transaction import Transaction

class Product(ModelSQL, ModelView):
    _name = 'product.product'

    attribute_values = fields.Many2Many('product.product-attribute.value',
        'product', 'value', 'Values', readonly=True)

    def __init__(self):
        super(Product, self).__init__()
        self.template.states = copy.copy(self.template.states)

        states = {
            'required':Greater(Eval('active_id', 0), 0),
            'invisible':Not(Greater(Eval('active_id', 0), 0)),
            'readonly':Not(Bool(Eval('variant')))
        }
        for state, pyson in states.iteritems():
            if not self.template.states.get(state):
                self.template.states[state] = pyson
            else:
                self.template.states[state] = \
                    Or(self.template.states[state],
                    pyson)

    def create(self, values):
        if values.get('template'):
            values = values.copy()
            values.pop('template')
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

    template_code = fields.Char('Template Code',
        required=True,
        states={
            'invisible': Not(Bool(Eval('attributes')))
            }, depends=['attributes'])
    attributes = fields.Many2Many('product.template-product.attribute',
        'template', 'attribute', 'Attributes')
    variant = fields.Function(fields.Boolean('Variant'),
        'get_variants', searcher='search_variants')
    template_description = fields.Text("Template Description", translate=True)

    def __init__(self):
        super(Template, self).__init__()
        self._rpc.update({
            'generate_variants': True,
        })
        #still here - but later in in product module
        for column in self._columns.itervalues():
            already = False
            column.states = copy.copy(column.states)
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

    def search_variants(self, name, clause):
        res = []
        cursor = Transaction().cursor
        cursor.execute('SELECT id FROM "' + self._table + '" WHERE True ')
        ids = [i[0] for i in cursor.fetchall()]
        records = self.browse(ids)
        if clause[2] == True:
            for template in records:
                if len(template.products) > 1:
                    res.append(template.id)
        else:
            for template in records:
                if len(template.products) <= 1:
                    res.append(template.id)
        return [('id', 'in', res)]

    def create_code(self, template_code, variant):
        "Create code based on template and attributes"
        config_obj = self.pool.get('product.variant.configuration')
        config = config_obj.browse(1)
        sep = config.code_separator or ''
        code = '%s%s' % (template_code or '', ['', sep][bool(template_code)])
        code = code + sep.join(i.code for i in variant)
        return code

    def create_product(self, template, variant):
        "Create product from template based on variant"
        product_obj = self.pool.get('product.product')
        value_obj = self.pool.get('product.product-attribute.value')
        code = self.create_code(template.template_code, variant)
        new_id = product_obj.create({'template':template.id,
            'code':code})
        for value in variant:
            value_obj.create({'product':new_id, 'value':value.id})
        return True

    def generate_variants(self, ids):
        """Generate variants"""
        if not ids:
            return {}
        res = {}
        for template in self.browse(ids):
            if not template.attributes:
                continue
            already = set(tuple(p.attribute_values) for p in template.products)
            values = [i.values for i in template.attributes]
            variants = itertools.product(*values)
            for variant in variants:
                if not variant in already:
                    self.create_product(template, variant)
        return res

Template()


class ProductAttribute(ModelSQL, ModelView):
    "Product Attribute"
    _name = "product.attribute"
    _description = __doc__

    sequence = fields.Integer('Sequence')
    name = fields.Char('Name', required=True, translate=True)
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
    name = fields.Char('Name', required=True, translate=True)
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
            ondelete='RESTRICT', required=True, select=True)
    template = fields.Many2One('product.template', 'Product template',
            ondelete='CASCADE', required=True, select=True)

ProductTemplateAttribute()


class ProductAttributeValue(ModelSQL, ModelView):
    "Product - Product Attribute Value"
    _name = "product.product-attribute.value"
    _description = __doc__

    product = fields.Many2One('product.product', 'Product',
            ondelete='CASCADE', required=True, select=True)
    value = fields.Many2One('product.attribute.value', 'Attribute Value',
            ondelete='RESTRICT', required=True, select=True)

ProductAttributeValue()
