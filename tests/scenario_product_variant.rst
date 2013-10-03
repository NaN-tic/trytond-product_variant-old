========================
Product Variant Scenario
========================

Imports::

    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install product_variant::

    >>> Module = Model.get('ir.module.module')
    >>> product_variant_module, = Module.find([('name', '=', 'product_variant')])
    >>> Module.install([product_variant_module.id], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create attribute::

    >>> Attribute = Model.get('product.attribute')
    >>> AttributeValue = Model.get('product.attribute.value')

    >>> attribute = Attribute()
    >>> attribute.name = 'Color'
    >>> attribute.save()

    >>> attribute_value = AttributeValue()
    >>> attribute_value.name = 'Red'
    >>> attribute_value.code = 'R'
    >>> attribute_value.attribute = attribute
    >>> attribute_value.save()

    >>> attribute_value = AttributeValue()
    >>> attribute_value.name = 'Black'
    >>> attribute_value.code = 'B'
    >>> attribute_value.attribute = attribute
    >>> attribute_value.save()

    >>> attribute = Attribute()
    >>> attribute.name = 'Size'
    >>> attribute.save()

    >>> attribute_value = AttributeValue()
    >>> attribute_value.name = 'Large'
    >>> attribute_value.code = 'L'
    >>> attribute_value.attribute = attribute
    >>> attribute_value.save()

    >>> attribute_value = AttributeValue()
    >>> attribute_value.name = 'Medium'
    >>> attribute_value.code = 'M'
    >>> attribute_value.attribute = attribute
    >>> attribute_value.save()

Create category::

    >>> ProductCategory = Model.get('product.category')
    >>> category = ProductCategory(name='Category')
    >>> category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> template = ProductTemplate()
    >>> template.name = 'Tryton T-Shirt'
    >>> template.category = category
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('10')
    >>> template.cost_price = Decimal('5')
    >>> template.cost_price_method = 'fixed'
    >>> template.basecode = '001-'
    >>> attributes = Attribute.find()
    >>> for attribute in attributes:
    ...     template.attributes.append(attribute)
    >>> template.save()
    >>> ProductTemplate.generate_variants([template.id], config.context)
    >>> Product = Model.get('product.product')
    >>> product, = Product.find([('code', '=', '001-RL')])
    >>> product.code
    u'001-RL'
