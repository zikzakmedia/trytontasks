#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import os
import xmltodict
import random
from decimal import Decimal
from trytond.pool import Pool
from utils import *

def create_product_category(name):
    """
    Creates product category with the supplied name.
    """
    Category = Pool().get('product.category')
    category = Category(name=name)
    category.save()

def create_product_categories(count=20):
    """
    Creates 'count' (20 by default) product categories.
    """
    Category = Pool().get('product.category')
    for name in ('A', 'B', 'C', 'D', 'E'):
        category = Category(name=name)
        category.save()

def create_product(name, code="", template=None, cost_price=None,
        list_price=None, type='goods', unit=None, consumable=False):
    """
    Create product
    """
    ProductUom = Pool().get('product.uom')
    Product = Pool().get('product.product')
    ProductTemplate = Pool().get('product.template')
    Category = Pool().get('product.category')

    if module_installed('account'):
        Tax = Pool().get('account.tax')

    categories = Category.search([])
    category = None
    if categories:
        category = random.choice(categories)

    product = Product.search([('name', '=', name), ('code', '=', code)])
    if product:
        return product[0]

    if not cost_price:
        cost_price = Decimal(random.randrange(1, 100))

    if not list_price:
        list_price = cost_price * (1 + Decimal(random.randrange(1, 100)) / 100)

    if unit is None:
        unit = ProductUom(1)

    if template is None:
        default_values = ProductTemplate.default_get(
            ProductTemplate._fields.keys(), with_rec_name=False)
        template = ProductTemplate(**default_values)
        template.name = name
        template.default_uom = unit
        template.type = type
        template.consumable = consumable
        template.list_price = list_price
        template.cost_price = cost_price
        template.categories = [category]

        if hasattr(template, 'salable'):
            template.salable = True
            template.sale_uom = unit
        if hasattr(template, 'purchasable'):
            template.purchasable = True
            template.purchase_uom = unit

        if (hasattr(template, 'account_expense')
                or hasattr(template, 'account_revenue')):
            Company = Pool().get('company.company')
            company = Company(1)
            template.accounts_category = False
            template.taxes_category = False
        if hasattr(template, 'account_expense'):
            Account = Pool().get('account.account')
            expense = Account.search([
                ('kind', '=', 'expense'),
                ('company', '=', company.id),
                ])
            if expense:
                template.account_expense = expense[0]
        if hasattr(template, 'account_revenue'):
            Account = Pool().get('account.account')
            revenue = Account.search([
                ('kind', '=', 'revenue'),
                ('company', '=', company.id),
                ])
            if revenue:
                template.account_revenue = revenue[0]
        if module_installed('account_es'):
            tax, = Tax.search([
                    ('template', '=',
                        get_object('account_es', 'iva_rep_21_pyme').id)
                    ])
            template.customer_taxes = [tax]
            tax, = Tax.search([
                    ('template', '=',
                        get_object('account_es', 'iva_sop_21_pyme').id)
                    ])
            template.supplier_taxes = [tax]
        elif module_installed('account_product'):
            taxes = Tax.search([], limit=1)
            if taxes:
                tax, = taxes
                template.customer_taxes = [tax]
            taxes = Tax.search([], limit=1)
            if taxes:
                tax, = taxes
                template.supplier_taxes = [tax]

        product = Product()
        product.code = code
        template.products = [product]
        template.save()
        product, = template.products
    else:
        product = Product()
        product.template = template
        product.code = code
        product.save()
    return product

def create_products(count=400):
    """
    Creates the 'count' first products from the icecat database in catalog.xml.
    """
    gal_dir = os.path.dirname(os.path.realpath(__file__))

    with open(gal_dir + '/product-catalog.xml', 'r') as f:
        xml = xmltodict.parse(f.read())
    i = 0
    for item in xml.get('ICECAT-interface').get('files.index').get('file'):
        name = item.get('@Model_Name')
        code = "PROD%05d" % i
        create_product(name, code)
        i += 1
        if i >= count:
            break

def create_price_lists(language='en', count=5, productcount=10, categorycount=2):
    """
    Creates 'count' pricelists using random products and quantities
    """
    PriceList = Pool().get('product.price_list')
    PriceListLine = Pool().get('product.price_list.line')
    Product = Pool().get('product.product')
    Category = Pool().get('product.category')
    category_module = module_installed('product_price_list_category')

    price_list_name = {
        'ca': 'Tarifa',
        'en': 'Price List',
        'es': 'Tarifa',
        }

    categories = Category.search([])
    if module_installed('sale'):
        domain = [('salable', '=', True)]
    else:
        domain = []
    products = Product.search(domain)
    for c in xrange(count):
        price_list = PriceList()
        price_list.name = price_list_name[language] +" "+ str(c)
        lines = []

        sequence = 1
        for lc in xrange(random.randrange(1, productcount)):
            line = PriceListLine()
            line.sequence = sequence
            line.product = random.choice(products)
            line.formula = 'unit_price * 0.90'
            lines.append(line)
            sequence += 1

        if category_module:
            for lc in xrange(random.randrange(1, categorycount)):
                line = PriceListLine()
                line.sequence = sequence
                line.category = random.choice(categories)
                line.formula = 'unit_price * 0.95'
                sequence += 1
                lines.append(line)

        line = PriceListLine()
        line.sequence = sequence
        line.formula = 'unit_price'
        lines.append(line)

        price_list.lines = lines
        price_list.save()
