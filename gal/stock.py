#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import random
from trytond.pool import Pool

def create_inventory(maxquantity=1000):
    """
    It randomly makes an inventory of 80% of existing products.

    The remaining 20% is left with existing stock (usually 0).

    A random value between 0 and maxquantity (1000 by default) will be used.
    """
    Inventory = Pool().get('stock.inventory')
    InventoryLine = Pool().get('stock.inventory.line')
    Location = Pool().get('stock.location')
    Product = Pool().get('product.product')

    location = Location.search([('type', '=', 'warehouse')])[0].storage_location

    inventory = Inventory()
    inventory.location = location
    inventory.save()
    products = Product.search([
            ('type', '=', 'goods'),
            ('consumable', '=', False),
            ])
    products = random.sample(products, int(0.8 * len(products)))

    inventory_lines = []
    for product in products:
        inventory_line = InventoryLine()
        inventory_line.product = product
        inventory_line.quantity = random.randrange(maxquantity)
        inventory_line.expected_quantity = 0.0
        inventory_lines.append(inventory_line)

    inventory.lines = inventory_lines
    inventory.save()
    Inventory.confirm([inventory])

def process_customer_shipments():
    """
    It randomly processes waiting customer shipments.

    20% of existing waiting customer shipments are left in waiting state
    80% are tried to be assigned (may not be assigned if stock is not enough)
    90% of the assigned ones are packed
    90% of the packed ones are done
    """
    Shipment = Pool().get('stock.shipment.out')
    shipments = Shipment.search([('state', '=', 'waiting')])

    shipments = random.sample(shipments, int(0.8 * len(shipments)))
    for shipment in shipments:
        Shipment.assign_try([shipment])
    shipments = random.sample(shipments, int(0.9 * len(shipments)))
    Shipment.pack(shipments)
    shipments = random.sample(shipments, int(0.9 * len(shipments)))
    Shipment.done(shipments)

def process_supplier_shipments():
    """
    It randomly processes waiting supplier shipments.

    10% of existing purchase orders are left processing
    90% are added to a shipment and set as received
    90% of those shipments are set as done
    """
    Shipment = Pool().get('stock.shipment.in')
    Purchase = Pool().get('purchase.purchase')

    shipments = []
    purchases = Purchase.search([('state', '=', 'confirmed')])
    purchases = random.sample(purchases, int(0.9 * len(purchases)))
    for purchase in purchases:
        shipment = Shipment()
        shipment.supplier = purchase.party
        shipment.save()
        shipments.append(shipment)
        for line in purchase.lines:
            for move in line.moves:
                # TODO: Improve performance, but append crashes
                #shipment.incoming_moves.append(move)
                move.shipment = shipment
                move.save()

    Shipment.receive(shipments)
    shipments = random.sample(shipments, int(0.9 * len(shipments)))
    Shipment.done(shipments)
