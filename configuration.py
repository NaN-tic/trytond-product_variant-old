#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.pyson import Eval

class Configuration(ModelSingleton, ModelSQL, ModelView):
    'Product Configuration'
    _name = 'product.variant.configuration'
    _description = __doc__

    identifier_seperator = fields.Property(fields.Char('Identifier seperator'))
    code_seperator = fields.Property(fields.Char('Code seperator'))

Configuration()
