#This file is part of trytontasks. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import os
from invoke import task
from proteus import config as pconfig, Model
from blessings import Terminal
import stdnum.eu.vat as vat
from .iban import create_iban, IBANError

t = Terminal()

@task
def convert_bank_accounts_to_iban(database):
    """
    Convert all Bank Account Numbers of type 'other' to 'iban'.
    """
    config_file = os.environ.get('TRYTOND_CONFIG', 'trytond.conf')

    print t.bold("Convert bank account number to IBAN")

    pconfig.set_trytond(database=database, config_file=config_file)

    BankAccount = Model.get('bank.account')
    bank_accounts = BankAccount.find([
            ('numbers.type', '=', 'other'),
            ])

    print "Total bank account number to IBAN: %s" % len(bank_accounts)

    for bank_account in bank_accounts:
        if any(n.type == 'iban' for n in bank_account.numbers):
            continue

        vat = bank_account.bank.party.vat_code
        if vat:
            vat_country = bank_account.bank.party.vat_code[:2]
        else:
            vat_country = 'ES'

        account_number = bank_account.numbers[0]
        number = account_number.number.replace(' ', '')
        try:
            iban = create_iban(
                vat_country,
                number[:8], number[8:])
        except IBANError, err:
            t.red("Error generating iban from number %s: %s" % (number, err))
            continue
        account_number.sequence = 10
        iban_account_number = bank_account.numbers.new()
        iban_account_number.type = 'iban'
        iban_account_number.sequence = 1
        iban_account_number.number = iban
        bank_account.save()

@task
def validate_vat(database):
    """
    Validate and compact VAT number
    """
    config_file = os.environ.get('TRYTOND_CONFIG', 'trytond.conf')

    print t.bold("Validate and compact VAT number")

    config = pconfig.set_trytond(database=database, config_file=config_file)

    Party = Model.get('party.party')
    Identifier = Model.get('party.identifier')

    parties = Party.find([
                ('vat_code', '!=', None),
            ])
    for p in parties:
        code = p.vat_code
        if not vat.is_valid(code):
            print t.red('Not valid: %s' % code)
            continue
        vat_compact = vat.compact(code)
        if vat_compact != code:
            identifier, = Identifier.find([
                ('code', '=', code),
                ('party', '=', p.id),
                ], limit=1)
            identifier.code = vat_compact
            identifier.save()
            print 'Compact VAT: %s' % vat_compact

@task
def calculate_sepa_identifier(database):
    """
    Calculate Sepa Creditor Identifier.
    """
    config_file = os.environ.get('TRYTOND_CONFIG', 'trytond.conf')

    print t.bold("Calculate Sepa Creditor Identifier")

    config = pconfig.set_trytond(database=database, config_file=config_file)

    PaymentType = Model.get('account.payment.type')
    Party = Model.get('party.party')

    payment_types = PaymentType.find([
                ('requires_sepa_creditor_identifier', '=', True),
            ])
    if not payment_types:
        print t.red("There are not payment types where Sepa is required")
        return

    # desactive pre-validation
    for p in payment_types:
        p.requires_sepa_creditor_identifier = False
        p.save()

    # parties by customer payments
    parties_customer = Party.find([
                ('customer_payment_type', 'in', [p.id for p in payment_types]),
                ('sepa_creditor_identifier', '=', None),
                ('vat_code', '!=', None),
            ])
    # parties by supplier payments - parties by customer payments
    parties_supplier = Party.find([
                ('customer_payment_type', 'in', [p.id for p in payment_types]),
                ('sepa_creditor_identifier', '=', None),
                ('vat_code', '!=', None),
                ('id', 'not in', [p.id for p in parties_customer]),
            ])
    parties = parties_customer + parties_supplier

    print "Total parties calculate Sepa Identifier: %s" % len(parties)

    # calculate sepa creditor identifier
    Party.calculate_sepa_creditor_identifier([x.id for x in parties], config.context)

    # reactive pre-validation
    for p in payment_types:
        p.requires_sepa_creditor_identifier = True
        p.save()
