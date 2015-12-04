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


class Product:
    __metaclass__ = PoolMeta
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
    __metaclass__ = PoolMeta
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
    def create_variant_code(cls, basecode, variant):
        Config = Pool().get('product.configuration')
        config = Config(1)
        sep = config.code_separator or ''
        code = '%s%s' % (basecode or '', ['', sep][bool(basecode)])
        code = code + sep.join(i.code for i in variant)
        return code

    def create_variant_product(self, variant):
        "Create the product from variant"
        pool = Pool()
        Product = pool.get('product.product')
        code = self.create_variant_code(self.basecode, variant)
        product, = Product.create([{
                    'template': self.id,
                    'code': code,
                    'attribute_values': [('add', [v.id for v in variant])],
                    }])
        return product

    def update_variant_product(self, products, variant):
        """Updates the code of supplied products with the code returned by
        create_code()"""
        pool = Pool()
        Product = pool.get('product.product')
        code = self.create_variant_code(self.basecode, variant)
        to_update = [p for p in products if p.code != code]
        if to_update:
            Product.write(to_update, {
                    'code': code,
                    })

    def deactivate_variant_product(self, products):
        """Deactivates supplied products"""
        pool = Pool()
        Product = pool.get('product.product')
        to_update = [p for p in products if p.active]
        if to_update:
            Product.write(to_update, {
                    'active': False,
                    })

    @classmethod
    @ModelView.button
    def generate_variants(cls, templates):
        """Generate variants"""
        Product = Pool().get('product.product')
        for template in templates:
            if not template.attributes:
                continue
            all_template_products = Product.search([
                    ('template', '=', template.id),
                    ('active', 'in', (True, False)),
                    ])
            products_by_attr_values = {}
            to_deactivate = []
            for product in all_template_products:
                if (product.attribute_values
                    and all([v.active for v in product.attribute_values])):
                        products_by_attr_values.setdefault(
                            tuple(product.attribute_values),
                            []).append(product)
                        continue
                to_deactivate.append(product)
            values = [a.values for a in template.attributes]
            for variant in itertools.product(*values):
                if variant in products_by_attr_values:
                    template.update_variant_product(
                        products_by_attr_values[variant], variant)
                else:
                    template.create_variant_product(variant)
            template.deactivate_variant_product(to_deactivate)


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
    active = fields.Boolean('Active', select=True)

    @classmethod
    def __setup__(cls):
        super(AttributeValue, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def default_sequence():
        return 0

    def deactivate(self, values):
        """Deactivates products attribute values"""
        pool = Pool()
        Product = pool.get('product.attribute.value')
        to_update = [p for p in values if p.active]
        if to_update:
            Product.write(to_update, {
                    'active': False,
                    })

    def activate(self, values):
        """Deactivates products attribute values"""
        pool = Pool()
        Product = pool.get('product.attribute.value')
        to_update = [p for p in values if not p.active]
        if to_update:
            Product.write(to_update, {
                    'active': True,
                    })


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
