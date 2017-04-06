#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.pool import Pool

def load_country_zip_es():
    'Loads zip codes from spain'
    LoadCountry = Pool().get('load.country.zips', type='wizard')

    session_id, _, _ = LoadCountry.create()
    load = LoadCountry(session_id)
    load.transition_accept()
