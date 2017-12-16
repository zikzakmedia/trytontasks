# encoding: utf-8
#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import datetime
import random
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from trytond.pool import Pool
from utils import *

TODAY = datetime.date.today()

def create_taxes():
    """
    Create Taxes
    """
    pool = Pool()
    Tax = pool.get('account.tax')
    Account = pool.get('account.account')

    accounts = Account.search([
        ('kind', 'not in', ['view', 'receivable', 'payable'])])

    tax = Tax()
    tax.name = '21%'
    tax.description = '21%'
    tax.rate = Decimal('0.21')
    tax.invoice_account = accounts[0]
    tax.credit_note_account = accounts[0]
    tax.save()

    tax2 = Tax()
    tax2.name = '10%'
    tax2.description = '10%'
    tax2.rate = Decimal('0.10')
    tax2.invoice_account = accounts[0]
    tax2.credit_note_account = accounts[0]
    tax2.save()

    return tax, tax2

def create_account_chart(company=None, module=None, fs_id=None, digits=None):
    """
    Creates the chart of accounts defined by module and fs_id for the given
    company.

    If no 'module' and 'fs_id' are given, the last template chart created is
    used.
    """
    pool = Pool()
    AccountTemplate = pool.get('account.account.template')
    Account = pool.get('account.account')
    Company = pool.get('company.company')
    ModelData = pool.get('ir.model.data')
    CreateChart = pool.get('account.create_chart', type='wizard')

    root_accounts = Account.search([('parent', '=', None)])
    if root_accounts:
        return

    if module and fs_id:
        data = ModelData.search([
                ('module', '=', module),
                ('fs_id', '=', fs_id),
                ], limit=1)

        assert len(data) == 1, ('Unexpected num of root templates '
            'with name "%s": %s' % (module, fs_id))
        template = data[0].db_id
        template = AccountTemplate(template)
    else:
        template, = AccountTemplate.search([('parent', '=', None)],
            order=[('id', 'DESC')], limit=1)

    if company:
        domain = [('party.name', '=', company),]
    else:
        domain =[]
    company, = Company.search(domain)

    session_id, _, _ = CreateChart.create()
    create_chart = CreateChart(session_id)
    create_chart.account.account_template = template
    create_chart.account.company = company
    if digits:
        create_chart.account.account_code_digits = digits
    create_chart.transition_create_account()
    receivable, = Account.search([
            ('kind', '=', 'receivable'),
            ('company', '=', company.id),
            ],
        limit=1)
    payable, = Account.search([
            ('kind', '=', 'payable'),
            ('company', '=', company.id),
            ],
        limit=1)
    create_chart.properties.company = company
    create_chart.properties.account_receivable = receivable
    create_chart.properties.account_payable = payable
    create_chart.transition_create_properties()

def create_fiscal_year(company=None, year=None):
    """
    Creates a new fiscal year with monthly periods and the appropriate
    invoice sequences for the given company.

    If no year is specified the current year is used.
    """
    pool = Pool()
    FiscalYear = pool.get('account.fiscalyear')
    Module = pool.get('ir.module')
    Sequence = pool.get('ir.sequence')
    SequenceStrict = pool.get('ir.sequence.strict')
    Company = pool.get('company.company')
    InvoiceSequence = pool.get('account.fiscalyear.invoice_sequence')

    if year is None:
        year = TODAY.year
    date = datetime.date(int(year), 1, 1)

    if company:
        domain = [('party.name', '=', company),]
    else:
        domain =[]
    company, = Company.search(domain, limit=1)

    installed_modules = [m.name
        for m in Module.search([('state', '=', 'activated')])]

    post_move_sequence = Sequence.search([
            ('name', '=', '%s' % year),
            ('code', '=', 'account_move'),
            ('company', '=', company.id),
            ])
    if post_move_sequence:
        post_move_sequence = post_move_sequence[0]
    else:
        post_move_sequence = Sequence(name='%s' % year,
            code='account.move', company=company)
        post_move_sequence.save()

    fiscalyear = FiscalYear.search([
            ('name', '=', '%s' % year),
            ('company', '=', company.id),
            ])
    if fiscalyear:
        fiscalyear = fiscalyear[0]
    else:
        fiscalyear = FiscalYear(name='%s' % year)
        fiscalyear.start_date = date + relativedelta(month=1, day=1)
        fiscalyear.end_date = date + relativedelta(month=12, day=31)
        fiscalyear.company = company
        fiscalyear.post_move_sequence = post_move_sequence
        if 'account_invoice' in installed_modules:
            invoice_sequence = InvoiceSequence()

            for attr, name in (('out_invoice_sequence', 'Customer Invoice'),
                    ('in_invoice_sequence', 'Supplier Invoice'),
                    ('out_credit_note_sequence', 'Customer Credit Note'),
                    ('in_credit_note_sequence', 'Supplier Credit Note')):
                sequence = SequenceStrict.search([
                        ('name', '=', '%s %s' % (name, year)),
                        ('code', '=', 'account.invoice'),
                        ('company', '=', company.id),
                        ])
                if sequence:
                    sequence = sequence[0]
                else:
                    sequence = SequenceStrict(
                        name='%s %s' % (name, year),
                        code='account.invoice',
                        company=company)
                    sequence.save()
                setattr(invoice_sequence, attr, sequence)
            fiscalyear.invoice_sequences = [invoice_sequence]
        fiscalyear.save()

    if not fiscalyear.periods:
        FiscalYear.create_period([fiscalyear])

    return fiscalyear

def create_payment_term(name, type='remainder', percentage=None, divisor=None,
        amount=None, day=None, month=None, weekday=None, months=0, weeks=0,
        days=0):
    """
    Creates a payment term with the supplied values.
    Default values are to create a Cash payment term
    """
    pool = Pool()
    Term = pool.get('account.invoice.payment_term')
    TermLine = pool.get('account.invoice.payment_term.line')

    term = Term()
    term.name = name
    term.active = True
    line = TermLine()
    line.type = type
    if percentage is not None:
        line.percentage = percentage
    if divisor is not None:
        line.divisor = divisor
    if amount is not None:
        line.amount = amount
    line.day = day
    line.month = month
    line.weekday = weekday
    line.months = months
    line.weeks = weeks
    line.days = days
    term.lines.append(line)
    term.save()

    return term

def create_payment_terms():
    """
    Creates 3 payment terms:
    - 30 days
    - 60 days
    - 90 days
    """
    PaymentTerm =  Pool().get('account.invoice.payment_term')

    PaymentTerm.create([{
        'name': '30 D',
        'lines': [
            ('create', [{
                'sequence': 0,
                'type': 'remainder',
                'relativedeltas': [('create', [{
                                'months': 1,
                                },
                            ]),
                    ],
                }])]
        }, {
        'name': '60 D',
        'lines': [
            ('create', [{
                'sequence': 0,
                'type': 'remainder',
                'relativedeltas': [('create', [{
                                'months': 2,
                                },
                            ]),
                    ],
                }])]
        }, {
        'name': '90 D',
        'lines': [
            ('create', [{
                'sequence': 0,
                'type': 'remainder',
                'relativedeltas': [('create', [{
                                'months': 3,
                                },
                            ]),
                    ],
                }])]
        }])

def create_payment_types(language='en'):
    """
    Creates payment types:
    - Bank Transfer
    - Direct Debit
    - Cash
    - Credit Card
    """
    Type =  Pool().get('account.payment.type')

    names = {
        'bank-transfer': {
            'ca': 'Transferència Bancària',
            'en': 'Bank Transfer',
            'es': 'Transferencia Bancaria',
            },
        'direct-debit': {
            'ca': 'Domiciliació bancària',
            'en': 'Direct Debit',
            'es': 'Domiciliación bancaria',
            },
        'cash': {
            'ca': 'Efectiu',
            'en': 'Cash',
            'es': 'Efectivo',
            },
        'credit-card': {
            'ca': 'Targeta de crèdit',
            'en': 'Credit Card',
            'es': 'Tarjeta de crédito',
            },
        }

    t = Type()
    t.name = names['bank-transfer'][language]
    t.kind = 'receivable'
    if hasattr(t, 'account_bank'):
        t.account_bank = 'company'
    t.save()

    t = Type()
    t.name = names['direct-debit'][language]
    t.kind = 'receivable'
    if hasattr(t, 'account_bank'):
        t.account_bank = 'party'
    t.save()

    t = Type()
    t.name = names['cash'][language]
    t.kind = 'receivable'
    if hasattr(t, 'account_bank'):
        t.account_bank = 'none'
    t.save()

    t = Type()
    t.name = names['bank-transfer'][language]
    t.kind = 'payable'
    if hasattr(t, 'account_bank'):
        t.account_bank = 'party'
    t.save()

    t = Type()
    t.name = names['direct-debit'][language]
    t.kind = 'payable'
    if hasattr(t, 'account_bank'):
        t.account_bank = 'company'
    t.save()

    t = Type()
    t.name = names['cash'][language]
    t.kind = 'payable'
    if hasattr(t, 'account_bank'):
        t.account_bank = 'none'
    t.save()

def process_customer_invoices():
    """
    It randomly confirms customer invoices.

    90% of customer invoices are confirmed.
    """
    Invoice =  Pool().get('account.invoice')

    payment_types = get_payment_types('receivable')

    invoices = Invoice.search([
            ('type', '=', 'out'),
            ('state', '=', 'draft'),
            ('payment_type.account_bank', '=', 'none'),
            ])
    invoices = random.sample(invoices, int(0.9 * len(invoices)))
    for invoice in invoices:
        # TODO: For consistency, better use the date of the maximum
        # date of the # sales composing the lines of the invoice
        invoice.invoice_date = random_datetime(
            TODAY + relativedelta(months=-12), TODAY)
        if hasattr(invoice, 'payment_type') and not invoice.payment_type:
            if invoice.party.customer_payment_type:
                invoice.payment_type = invoice.party.customer_payment_type
            else:
                if payment_types:
                    invoice.payment_type = random.choice(payment_types)
        invoice.save()

    Invoice.post(invoices)
