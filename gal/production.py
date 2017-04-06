#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import random
from trytond.pool import Pool

def create_boms(name='pc', inputcount=10, inputquantity=10):
    """
    Creates boms for all products that contain the word 'name' in their name.

    It creates between 1 and inputcount inputs with quantity between 1 and
    inputquantity.

    If name is empty it creates boms for 20% of the products available in the
    database.
    """

    Product = Pool().get('product.product')
    BOM = Pool().get('production.bom')
    Input = Pool().get('production.bom.input')
    Output = Pool().get('production.bom.output')
    ProductBOM = Pool().get('product.product-production.bom')

    products = Product.search([])
    products = [x.id for x in products]
    if name:
        to_produce = Product.search([('name', 'ilike', '%' + name + '%')])
    else:
        to_produce = random.sample(products, int(0.2 * len(products)))
        to_produce = Product.search([('id', 'in', to_produce)])
    to_purchase = Product.search([('id', 'not in', [x.id for x in to_produce])])
    for product in to_produce:
        product.purchasable = False

        bom = BOM()
        bom.name = ''
        if product.code:
            bom.name = '[%s] ' % product.code
        bom.name += product.template.name

        # Use sample because product must be unique per BOM
        bom_inputs = []
        for input_product in random.sample(to_purchase, random.randrange(1, inputcount)):
            input_ = Input()
            input_.product = input_product
            input_.quantity = random.randrange(1, inputquantity)
            input_.on_change_product()
            bom_inputs.append(input_)
        bom.inputs = bom_inputs

        output = Output()
        output.product = product
        output.quantity = 1
        output.on_change_product()
        bom.outputs = [output]
        bom.save()

        pb = ProductBOM()
        pb.bom = bom
        product.boms = [pb]
        product.save()

def create_production_requests():
    CreateRequest = Pool().get('production.create_request', type='wizard')

    # TODO create order points
    session_id, _, _ = CreateRequest.create()
    load = CreateRequest(session_id)
    load.transition_create_()
