#This file is part product_variant module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Not, Bool
from trytond.transaction import Transaction
import itertools

__all__ = ['Product', 'Template', 'ProductAttribute', 'AttributeValue',
    'ProductTemplateAttribute', 'ProductAttributeValue']
__metaclass__ = PoolMeta


class Product:
    __name__ = 'product.product'
    attribute_values = fields.Many2Many('product.product-attribute.value',
        'product', 'value', 'Values', readonly=True,
        order=[('value', 'DESC')])

    @classmethod
    def create(cls, vlist):
        for vals in vlist:
            if vals.get('template') and not vals['template']:
                vals = vals.copy()
                vals.pop('template')
        return super(Product, cls).create(vlist)


class Template:
    __name__ = 'product.template'
    basecode = fields.Char('Basecode',
        states={
            'invisible': Not(Bool(Eval('attributes')))
        }, depends=['attributes'])
    attributes = fields.Many2Many('product.template-product.attribute',
        'template', 'attribute', 'Attributes')
    variants = fields.Function(fields.Integer('Variants', select=1,
        help='Number variants from this template'),
        'get_variants', searcher='search_variants')

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()
        cls._buttons.update({
                'generate_variants': {
                    'invisible': Eval('template'),
                    }
            })

    @classmethod
    def delete(cls, templates):
        #don't know - but this prevent always the deleation of the template
        #so the user has to delete empty templates manually
        templates = list(set(templates))
        if Transaction().delete:
            return templates
        return super(Template, cls).delete(templates)

    def get_variants(self, name=None):
        variants = len(self.products)
        if variants <= 1:
            variants = None
        return variants

    @classmethod
    def search_variants(cls, name, clause):
        res = []
        for template in cls.search([]):
            if len(template.products) >= clause[2]:
                res.append(template.id)
        return [('id', 'in', res)]

    @classmethod
    def create_code(self, basecode, variant):
        Config = Pool().get('product.variant.configuration')
        config = Config(1)
        sep = config.code_separator or ''
        code = '%s%s' % (basecode or '', ['', sep][bool(basecode)])
        code = code + sep.join(i.code for i in variant)
        return code

    @classmethod
    def create_product(self, template, variant):
        "Create the product from variant"
        pool = Pool()
        Product = pool.get('product.product')
        Value = pool.get('product.product-attribute.value')
        code = self.create_code(template.basecode, variant)
        product = Product.create([{'template': template.id, 'code': code}])[0]
        to_create = []
        for value in variant:
            to_create.append({'product': product, 'value': value.id})
        if to_create:
            Value.create(to_create)
        return True

    @classmethod
    @ModelView.button
    def generate_variants(cls, templates):
        """generate variants"""
        for template in templates:
            if not template.attributes:
                continue
            already = set(tuple(i.attribute_values) for i in template.products)
            to_del = [i for i in template.products if not i.attribute_values]
            values = [i.values for i in template.attributes]
            variants = itertools.product(*values)
            for variant in variants:
                if not variant in already:
                    cls.create_product(template, variant)
            Pool().get('product.product').delete(to_del)


class ProductAttribute(ModelSQL, ModelView):
    "Product Attribute"
    __name__ = "product.attribute"
    sequence = fields.Integer('Sequence')
    name = fields.Char('Name', required=True, translate=True, select=1)
    values = fields.One2Many('product.attribute.value', 'attribute', 'Values')

    @classmethod
    def __setup__(cls):
        super(ProductAttribute, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def order_sequence(tables):
        table, _ = tables[None]
        return [table.sequence == None, table.sequence]


class AttributeValue(ModelSQL, ModelView):
    "Values for Attributes"
    __name__ = "product.attribute.value"
    sequence = fields.Integer('Sequence')
    name = fields.Char('Name', required=True, select=1)
    code = fields.Char('Code', required=True)
    attribute = fields.Many2One('product.attribute', 'Product Attribute',
        required=True, ondelete='CASCADE')

    @classmethod
    def __setup__(cls):
        super(AttributeValue, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def default_sequence():
        return 0


class ProductTemplateAttribute(ModelSQL, ModelView):
    "Product Template - Product Attribute"
    __name__ = "product.template-product.attribute"
    attribute = fields.Many2One('product.attribute', 'Product Attribute',
            ondelete='RESTRICT', required=True)
    template = fields.Many2One('product.template', 'Product template',
            ondelete='CASCADE', required=True)


class ProductAttributeValue(ModelSQL, ModelView):
    "Product - Product Attribute Value"
    __name__ = "product.product-attribute.value"
    product = fields.Many2One('product.product', 'Product',
            ondelete='CASCADE', required=True)
    value = fields.Many2One('product.attribute.value', 'Attribute Value',
            ondelete='CASCADE', required=True)

    @classmethod
    def search(cls, args, offset=0, limit=None, order=None, count=False,
            query=False):
        '''Order attributes value by sequence'''
        res = super(ProductAttributeValue, cls).search(args, offset, limit,
            order, count, query)
        obs = [(ob.value.attribute.sequence, ob.id) for ob in res]
        obs.sort()
        res = [cls(i[1]) for i in obs]
        return res
