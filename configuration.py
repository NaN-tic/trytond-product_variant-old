#This file is part product_variant module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, ModelSingleton, fields


__all__ = ['Configuration']


class Configuration(ModelSingleton, ModelSQL, ModelView):
    'Variant Configuration'
    __name__ = 'product.variant.configuration'

    code_separator = fields.Char('Code Separator')

