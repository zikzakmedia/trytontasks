#!/usr/bin/env python
# encoding: utf-8
import optparse
import socket
import sys
import os
import logging
from decimal import Decimal
from blessings import Terminal

from utils import get_modules
from bank import load_bank_es
from country import load_country_zip_es
from company import *
from account import *
from electronic_mail import *

def parse_arguments(arguments):
    parser = optparse.OptionParser(usage='%s [options]' % __name__)
    parser.add_option('-d', '--database', dest='database',
            help='Database to get modules installed')
    parser.add_option('-c', '--config-file', dest='config',
            help='Config File to update modules (optional)')
    parser.add_option('-m', '--modules', dest='modules',
            help='Modules to install (optional)')
    (option, arguments) = parser.parse_args(arguments)

    # Remove first argument because it's application name
    arguments.pop(0)

    return option

t = Terminal()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Get arguments
options = parse_arguments(sys.argv)
dbname = options.database
if not dbname:
    sys.exit("Missing database parameter")
config_file = options.config if options.config \
    else os.environ.get('TRYTOND_CONFIG',
        './etc/server-%s.cfg' % socket.gethostname())

logger.info('Database: %s' % dbname)
logger.info('Configuration file: %s' % config_file)

# Start to import trytond
from trytond.config import config as CONFIG
CONFIG.update_etc(config_file)

from trytond.transaction import Transaction
from trytond.pool import Pool
# from trytond.model import EvalEnvironment
from trytond.pyson import Eval, If, Id, PYSONEncoder, PYSONDecoder

Pool.start()
pool = Pool(dbname)
pool.init()

context = {
    'active_test': False,
    'language': 'en',
    # 'company': 1,
}

logger.info('Start config modules')

with Transaction().start(dbname, 1, context=context):
    Module = pool.get('ir.module')
    ModuleConfig = pool.get('ir.module.config_wizard.item')
    Company = pool.get('company.company')

    if options.modules:
        modules = options.modules.split(',')
    else:
        modules = get_modules().get('to_activated', [])

    modules_activated = [m.name for m in Module.search([
            ('name', 'in', modules),
            ('state', '=', 'activated'),
            ])]

    if 'bank_es' in (modules_activated and modules):
        logger.info('Load Spanish Banks...')
        load_bank_es()

    if 'country_zip_es' in (modules_activated and modules):
        logger.info('Load Spanish cities and subdivisions...')
        load_country_zip_es()

    if 'company' in (modules_activated and modules):
        logger.info('Create company...')
        create_company('TrytonERP')

    company, = Company.search([], limit=1)
    company_id = company.id


context['company'] = company_id
with Transaction().start(dbname, 1, context=context):

    if 'account' in (modules_activated and modules):
        logger.info('Create accounts...')
        last_year = TODAY.year -1
        create_fiscal_year(year=last_year)
        create_fiscal_year()
        create_payment_terms()
        if 'account_es' in (modules_activated and modules):
            module = 'account_es'
            fs_id = 'pgc_0'
        elif 'account_es_pyme' in (modules_activated and modules):
            module = 'account_es_pyme'
            fs_id = 'pgc_pymes_0'
        else:
            module = 'account'
            fs_id = 'account_template_root_%s' % language
        create_account_chart(module=module, fs_id=fs_id, digits=6)


    if 'account_payment_type' in (modules_activated and modules):
        logger.info('Create payment types...')
        create_payment_types(language='es')

    if 'electronic_mail' in (modules_activated and modules):
        logger.info('Create electronic mail templates...')
        create_email_templates()

    configs = ModuleConfig.search([])
    ModuleConfig.write(configs, {'state': 'done'})

    Transaction().commit()

logger.info('End config modules')
