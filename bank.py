#This file is part of trytontasks. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import os
from invoke import task
from proteus import config as pconfig, Model
from blessings import Terminal
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
                number[:8], number[10:])
        except IBANError, err:
            t.red("Error generating iban from number %s: %s" % (number, err))
            continue
        account_number.sequence = 10
        iban_account_number = bank_account.numbers.new()
        iban_account_number.type = 'iban'
        iban_account_number.sequence = 1
        iban_account_number.number = iban
        bank_account.save()
