#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import datetime
from dateutil.relativedelta import relativedelta
from trytond.pool import Pool
from .utils import *
from .party import create_party

TODAY = datetime.date.today()

def create_opportunities(count=100, linecount=10):
    """
    It randomly creates leads and opportunities

    It creates 'count' leads.
    - It converts 80% of the converted leads into opportunities
    - It converts 40% of the opportunities as lost
    - It sets 80% of the remaining opportunities are converted.
    """
    Opportunity = Pool().get('sale.opportunity')
    OpportunityLine = Pool().get('sale.opportunity.line')
    Product = Pool().get('product.product')
    Party = Pool().get('party.party')
    Term = Pool().get('account.invoice.payment_term')
    Employee = Pool().get('company.employee')

    parties = Party.search([])
    products = Product.search([('salable', '=', True)])
    terms = Term.search([])

    employees = Employee.search([], limit=1)
    if employees:
        employee, = employees
    else:
        party = create_party(name='Raimon')
        employee = Employee()
        employee.party = party
        employee.save()

    for x in range(count):
        opp = Opportunity()
        party = random.choice(parties)
        product = random.choice(products)
        opp.description = '%s - %s' % (party.rec_name, product.rec_name)
        opp.party = party
        if party.addresses:
            opp.address = party.addresses[0]
        opp.start_date = random_datetime(TODAY + relativedelta(months=-12),
            TODAY)
        opp.on_change_party()
        if not opp.payment_term:
            opp.payment_term = random.choice(terms)
        opp.probability = random.randrange(1, 9) * 10
        opp.amount = random.randrange(1, 10) * 1000
        opp.employee = employee

        lines = []
        for lc in range(random.randrange(1, linecount)):
            line = OpportunityLine()
            line.product = random.choice(products)
            line.quantity = random.randrange(1, 20)
            line.on_change_product()
            lines.append(line)

        opp.lines = lines
        opp.save()

def process_opportunities():
    """
    It randomly processes leads

    - It converts 80% of the leads into opportunities
    - It converts 40% of the opportunities as lost
    - It sets 80% of the remaining opportunities as converted (sale created)
    """
    Opportunity = Pool().get('sale.opportunity')

    opps = Opportunity.search([('state', '=', 'lead')])
    opps = random.sample(opps, int(0.8 * len(opps)))
    if opps:
        Opportunity.opportunity(opps)

    lost = random.sample(opps, int(0.4 * len(opps)))
    if lost:
        Opportunity.lost(lost)

    # Only convert non-lost opportunities
    nopps = []
    for opp in opps:
        if opp in lost:
            continue
        nopps.append(opp)
    opps = nopps
    opps = random.sample(opps, int(0.8 * len(opps)))
    opps = [Opportunity(x) for x in opps]
    if opps:
        Opportunity.convert(opps)
