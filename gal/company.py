#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from party import create_party

def create_company(name, currency_code='EUR'):
    """
    Creates a company in current gal database.

    Based on tryton_demo.py in tryton-tools repo:
    http://hg.tryton.org/tryton-tools
    """
    Company = Pool().get('company.company')
    Currency = Pool().get('currency.currency')
    Party = Pool().get('party.party')
    CreateCompany = Pool().get('company.company.config', type='wizard')

    party = Party()
    party.name = name
    party.save()

    currency, = Currency.search([('code', '=', currency_code)])

    session_id, _, _ = CreateCompany.create()
    create_company = CreateCompany(session_id)
    create_company.company.party = party
    create_company.company.currency = currency
    create_company.transition_add()

def create_employee(name, company=None, user=None):
    """
    Creates the employee with the given name in the given company and links
    it with the given user.

    If company is not set the first company found on the system is used.
    If user is not set, 'admin' user is used.
    """
    Company = Pool().get('company.company')
    Employee = Pool().get('company.employee')
    Party = Pool().get('party.party')
    User = Pool().get('res.user')

    if user is None:
        user = 'admin'
    if company:
        company, = Company.search([('name', '=', company)])
    else:
        company, = Company.search([], limit=1)

    party = Party()
    party.name = name
    party.save()

    employee = Employee()
    employee.party = party
    employee.company = company
    employee.save()

    user, = User.search([('login', '=', user)], limit=1)
    user.employees.append(employee)
    user.employee = employee
    user.save()
