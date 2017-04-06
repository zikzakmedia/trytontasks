#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.pool import Pool

def load_bank_es():
    'Loads all banks from spain'
    LoadBank = Pool().get('load.banks', type='wizard')

    session_id, _, _ = LoadBank.create()
    load = LoadBank(session_id)
    load.transition_accept()
