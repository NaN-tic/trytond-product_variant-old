#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
{
    'name': 'Product Variants',
    'version': '2.3.0',
    'author': 'grasbauer',
    'email': 'info@grasbauer.com',
    'website': 'http://www.grasbauer.com/',
    'description': """Manage variants of products with automatic 
generation based on attributes.""",
    'depends': [
        'ir',
        'res',
        'product',
    ],
    'xml': [
        'configuration.xml',
        'product.xml',
    ]
}

