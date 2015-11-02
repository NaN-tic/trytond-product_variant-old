# This file is part product_variant module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool
from .configuration import *
from .product import *


def register():
    Pool.register(
        Configuration,
        Product,
        Template,
        ProductAttribute,
        AttributeValue,
        ProductTemplateAttribute,
        ProductAttributeValue,
        module='product_variant', type_='model')
