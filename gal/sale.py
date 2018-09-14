#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import datetime
import logging
from dateutil.relativedelta import relativedelta
from trytond.pool import Pool
from .utils import *

TODAY = datetime.date.today()
logger = logging.getLogger(__name__)

def create_sales(count=100, linecount=10):
    """
    It creates 'count' sales using random products (linecount maximum)
    and parties.

    If 'count' is not specified 100 is used by default.
    If 'linecount' is not specified 10 is used by default.
    """
    Sale = Pool().get('sale.sale')
    SaleLine = Pool().get('sale.line')
    Party = Pool().get('party.party')
    Product = Pool().get('product.product')
    Term = Pool().get('account.invoice.payment_term')
    PaymentType = Pool().get('account.payment.type')

    parties = Party.search([])
    products = Product.search([('salable', '=', True)])
    if not products:
        logger.info('Not found salable products')
        return

    terms = Term.search([])
    payments = PaymentType.search([('kind', 'in', ['both', 'receivable'])])

    default_values = Sale.default_get(
        list(Sale._fields.keys()), with_rec_name=False)
    default_lvalues = SaleLine.default_get(
        list(SaleLine._fields.keys()), with_rec_name=False)

    for c in range(count):
        sale = Sale(**default_values)
        sale.sale_date = random_datetime(TODAY + relativedelta(months=-12),
            TODAY)
        sale.party = random.choice(parties)
        sale.on_change_party()
        if not sale.payment_term:
            sale.payment_term = random.choice(terms)
        if not sale.payment_type:
            sale.payment_type = random.choice(payments)

        lines = []
        for lc in range(random.randrange(1, linecount)):
            line = SaleLine(**default_lvalues)
            line.product = random.choice(products)
            line.quantity = random.randrange(1, 20)
            line.on_change_product()
            lines.append(line)

        sale.lines = lines
        sale.save()

def process_sales():
    """
    It randomly processes some sales:

    10% of existing draft sales are left in draft state
    10% of existing draft sales are left in quotation state
    10% of existing draft sales are left in confirmed state
    70% of existing draft sales are left in processed state
    """
    Sale = Pool().get('sale.sale')

    sales = Sale.search([('state', '=', 'draft')])
    if not sales:
        logger.info('Not found draft sales')
        return
    #TODO: Put random sale dates
    # sale.sale_date = random_datetime(TODAY + relativedelta(months=-12),
    #        TODAY)

    # Change 90% to quotation state
    sales = random.sample(sales, int(0.9 * len(sales)))
    Sale.quote(sales)

    # Change 90% to confirmed state
    sales = random.sample(sales, int(0.9 * len(sales)))
    Sale.confirm(sales)

    # Change 90% to processed state
    sales = random.sample(sales, int(0.9 * len(sales)))
    Sale.process(sales)
