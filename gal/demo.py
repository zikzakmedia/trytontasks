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
from party import *
from product import *
from sale import *
from sale_opportunity import *
from purchase import *
from production import *
from stock import *
from account import *

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
    # 'active_test': True,
    'language': 'en',
    'company': 1, # TODO multicompany
}

logger.info('Start demo data')

with Transaction().start(dbname, 1, context=context):
    Module = pool.get('ir.module')

    if options.modules:
        modules = options.modules.split(',')
    else:
        modules = get_modules().get('to_activated', [])

    modules_activated = [m.name for m in Module.search([
            ('name', 'in', modules),
            ('state', '=', 'activated'),
            ])]

    # # Demo data
    if 'product' in (modules_activated and modules):
        logger.info('Create products...')
        create_product_categories()
        create_products()
    if 'product_price_list' in (modules_activated and modules):
        logger.info('Create price lists...')
        create_price_lists(language='es')
    if 'party' in (modules_activated and modules):
        logger.info('Create parties...')
        create_parties()
    if 'sale' in (modules_activated and modules):
        logger.info('Create sales...')
        create_sales()
        logger.info('Process sales...')
        process_sales()
    if 'sale_opportunity' in (modules_activated and modules):
        logger.info('Create sale opportunities...')
        create_opportunities()
        logger.info('Process opportunities...')
        process_opportunities()
    if 'purchase' in (modules_activated and modules):
        logger.info('Create purchases...')
        create_purchases()
        logger.info('Process purchases...')
        process_purchases()
    if 'production' in (modules_activated and modules):
        logger.info('Create productions...')
        create_boms()
    if 'stock_supply_production' in (modules_activated and modules):
        logger.info('Create productions requests...')
        create_production_requests()
    if 'stock' in (modules_activated and modules):
        logger.info('Create Stock Inventory...')
        create_inventory()
        logger.info('Create Stock Shipments...')
        process_customer_shipments()
        process_supplier_shipments()
    if 'account_invoice' in (modules_activated and modules):
        logger.info('Process Customer Invoices...')
        process_customer_invoices()

    Transaction().commit()

logger.info('End demo data')
