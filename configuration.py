#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields

class Configuration(ModelSingleton, ModelSQL, ModelView):
    'Variant Configuration'
    _name = 'product.variant.configuration'
    _description = __doc__

    code_separator = fields.Char('Code Separator')

Configuration()
