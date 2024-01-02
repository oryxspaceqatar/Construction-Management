{
    'name': "Sale Extend",
    'version': '17.0.1.0.1',
    'depends': ['base', 'sale','sales_team','purchase','construction_management'],
    'data': [
        'security/security.xml',
        'data/mail_template.xml',
        'views/sale_order.xml',
        'views/sale_invoice.xml',
        'views/material_requisition.xml',
        'views/purchase_order.xml',

    ],
    'license': "AGPL-3",
    'installable': True,
    'application': False,
}
