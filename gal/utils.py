#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import random
import yaml
from datetime import timedelta
from functools32 import lru_cache
from trytond.pool import Pool

def get_modules():
    config = yaml.load(open('tasks/gal/trytond-modules.yml', 'r').read())
    config.setdefault('to_activated', [])
    return config

def random_datetime(start, end):
    """
    This function will return a random datetime between two datetime
    objects.
    """
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)

@lru_cache()
def module_installed(module):
    Module = Pool().get('ir.module')
    return bool(Module.search([
            ('name', '=', module),
            ('state', '=', 'activated'),
            ]))

@lru_cache()
def get_account_payable():
    Payable = Pool().get('account.account')
    return Payable.search([('kind', '=', 'payable')])

@lru_cache()
def get_account_receivable():
    Receivable = Pool().get('account.account')
    return Receivable.search([('kind', '=', 'receivable')])

@lru_cache()
def get_payment_terms():
    Term = Pool().get('account.invoice.payment_term')
    return Term.search([])

@lru_cache()
def get_payment_types(kind):
    Type = Pool().get('account.payment.type')
    return Type.search([('kind', '=', kind)])

@lru_cache()
def get_languages():
    Lang = Pool().get('ir.lang')
    return Lang.search([
            ('code', 'in', ['ca', 'es', 'en']),
            ])

@lru_cache()
def get_price_lists():
    PriceList = Pool().get('product.price_list')
    return PriceList.search([])

@lru_cache()
def get_banks():
    if not module_installed('bank'):
        return
    Bank = Pool().get('bank')
    return Bank.search([])

@lru_cache()
def get_company():
    Company = Pool().get('company.company')
    companies = Company.search([])
    if companies:
        return companies[0]

@lru_cache()
def get_model_id(module, fs_id):
    ModelData = Pool().get('ir.model.data')
    data, = ModelData.search([
            ('module', '=', module),
            ('fs_id', '=', fs_id),
            ])
    return data.model, data.db_id

def get_object(module, fs_id):
    model, id = get_model_id(module, fs_id)
    Class = Pool().get(model)
    return Class(id)
