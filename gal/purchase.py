#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import datetime
import logging
from dateutil.relativedelta import relativedelta
from trytond.pool import Pool
from utils import *

TODAY = datetime.date.today()
logger = logging.getLogger(__name__)

def create_purchases(count=100, linecount=10):
    """
    It creates 'count' purchases using random products (linecount maximum)
    and parties.

    If 'count' is not specified 100 is used by default.
    If 'linecount' is not specified 10 is used by default.
    """
    Purchase = Pool().get('purchase.purchase')
    PurchaseLine = Pool().get('purchase.line')
    Party = Pool().get('party.party')
    Product = Pool().get('product.product')
    Term = Pool().get('account.invoice.payment_term')

    parties = Party.search([])
    products = Product.search([('purchasable', '=', True)])
    if not products:
        logger.info('Not found purchasable products')
        return
    terms = Term.search([])

    for c in range(count):
        purchase = Purchase()
        purchase.party = random.choice(parties)
        purchase.on_change_party()
        if not purchase.payment_term:
            purchase.payment_term = random.choice(terms)

        lines = []
        for lc in range(random.randrange(1, linecount)):
            line = PurchaseLine()
            line.product = random.choice(products)
            line.quantity = random.randrange(1, 20)
            line.on_change_product()
            lines.append(line)

        purchase.lines = lines
        purchase.save()

def process_purchases():
    """
    It randomly processes some purchases:

    10% of existing draft purchases are left in draft state
    10% of existing draft purchases are left in quotation state
    80% of existing draft purchases are left in confirmed state
    """
    Purchase = Pool().get('purchase.purchase')

    purchases = Purchase.search([
        ('state', '=', 'draft'),
        ('invoice_address', '!=', None),
        ])
    if not purchases:
        logger.info('Not found draft purchases')
        return
    # Change 90% to quotation state
    purchases = random.sample(purchases, int(0.9 * len(purchases)))
    Purchase.quote(purchases)

    # Change 90% to confirmed state
    purchases = random.sample(purchases, int(0.9 * len(purchases)))
    Purchase.confirm(purchases)
