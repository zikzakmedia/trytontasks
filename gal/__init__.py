#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import datetime
import os
import logging
import random
import socket
import sys
import yaml
from invoke import Collection, task, run
from blessings import Terminal
from proteus import Model, Wizard
from proteus import config as pconfig_
from trytond.config import config, parse_uri

from .utils import *
from .company import *
from .bank import *
from .country import *
from .account import *
from .party import *
from .product import *
from .sale import *
from .sale_opportunity import *
from .purchase import *
from .production import *
from .stock import *

t = Terminal()
logger = logging.getLogger(__name__)
TODAY = datetime.date.today()

def set_config(database, password):
    os.environ['DB_NAME'] = database
    database = 'postgresql://%s' % database
    return pconfig_.set_trytond(
        database=database,
        user='admin',
        config_file='./etc/server-%s.cfg' % socket.gethostname())

def get_modules():
    config = yaml.load(open('tasks/gal/trytond-modules.yml', 'r').read())
    config.setdefault('to_activated', [])
    return config

def install_modules(config, modules):
    Module = Model.get('ir.module')

    if not modules:
        modules = get_modules().get('to_activated', [])
    logger.info(t.green('Modules to install: %s' % ', '.join(modules)))

    modules = Module.find([
            ('name', 'in', modules),
            ])
    for module in modules:
        if module.state == 'activated':
            module.click('upgrade')
        else:
            module.click('activate')
    modules = [x.name for x in Module.find([('state', '=', 'to activate')])]
    Wizard('ir.module.activate_upgrade').execute('upgrade')

    ConfigWizardItem = Model.get('ir.module.config_wizard.item')
    for item in ConfigWizardItem.find([('state', '!=', 'done')]):
        item.state = 'done'
        item.save()

    installed_modules = [m.name
        for m in Module.find([('state', '=', 'activated')])]
    return modules, installed_modules


@task()
def create(ctx, database, password='admin'):
    'Create trytond database and langs. The DB must created with createdb psql.'
    logger.info('Create DB %s' % database)

    command = 'trytond/bin/trytond-admin -v -c %(config)s --all -d %(database)s -l es' % {
        'config': './etc/server-%s.cfg' % socket.gethostname(),
        'database': database,
        }
    run(command)

    # After trytond-admin we could do proteus tasks
    pconfig = set_config(database, password)

    Lang = Model.get('ir.lang')
    User = Model.get('res.user')

    # Set langs translatable
    ca, es = Lang.find([
            ('code', 'in', ['es', 'ca']),
            ])
    ca.translatable = True
    ca.save()
    es.translatable = True
    es.save()

    # Set lang in admin user
    admin, = User.find([
            ('login', '=', 'admin'),
            ], limit=1)
    admin.language = es
    admin.save()

@task()
def install(ctx, database, password='admin', modules=None, data=False):
    'Install modules and create data'
    pconfig = set_config(database, password)
    context = pconfig.context
    language = context.get('language', 'es')
    # TODO modules args list parameters
    # https://github.com/pyinvoke/invoke/issues/132
    if modules:
        modules = modules.split(' ')

    to_install, installed = install_modules(pconfig, modules)

    if 'bank_es' in to_install:
        logger.info('Load Spanish Banks...')
        load_bank_es()
    if 'country_zip_es' in to_install:
        logger.info('Load Spanish cities and subdivisions...')
        load_country_zip_es()
    if 'company' in to_install:
        logger.info('Create company...')
        create_company(pconfig, 'TrytonERP')
    if 'account' in to_install:
        logger.info('Create accounts...')
        last_year = TODAY.year -1
        create_fiscal_year(config=pconfig, year=last_year)
        create_fiscal_year(config=pconfig)
        create_payment_terms()
        if 'account_es' in to_install:
            module = 'account_es'
            fs_id = 'pgc_0'
        elif 'account_es_pyme' in to_install:
            module = 'account_es_pyme'
            fs_id = 'pgc_pymes_0'
        else:
            module = 'account'
            fs_id = 'account_template_root_%s' % language
        create_account_chart(module=module, fs_id=fs_id, digits=6)
        create_taxes()
    if 'account_payment_type' in to_install:
        logger.info('Create payment types...')
        create_payment_types(language=language)

    if not data:
        return

    # Demo data
    if 'party' in to_install:
        logger.info('Create parties...')
        create_parties()
    if 'product' in to_install:
        logger.info('Create products...')
        create_product_categories()
        create_products()
    if 'product_price_list' in to_install:
        logger.info('Create price lists...')
        create_price_lists(language=language)
    if 'sale' in to_install:
        logger.info('Create sales...')
        create_sales()
        process_sales(config=pconfig)
    if 'sale_opportunity' in to_install:
        logger.info('Create sale opportunities...')
        create_opportunities()
        process_opportunities()
    if 'purchase' in to_install:
        logger.info('Create purchases...')
        create_purchases()
        process_purchases(config=pconfig)
    if 'production' in to_install:
        logger.info('Create productions...')
        create_boms()
        create_production_requests()
    if 'stock' in to_install:
        logger.info('Create Stock Inventory...')
        create_inventory(config=pconfig)
        logger.info('Create Stock Shipments...')
        process_customer_shipments(config=pconfig)
        process_supplier_shipments(config=pconfig)
    if 'account_invoice' in to_install:
        logger.info('Process Customer Invoices...')
        process_customer_invoices(config=pconfig)

@task()
def dump(ctx, database):
    'Dump PSQL Database to SQL file'
    config.update_etc('./etc/server-%s.cfg' % socket.gethostname())
    uri = config.get('database', 'uri')

    logger.info("Dump PSQL database: " + t.green(database))

    command = 'pg_dump -d %(database)s -U %(username)s > ./psql_%(database)s.sql' % {
        'database': database,
        'username': parse_uri(uri).username,
        }
    run(command)

@task()
def restore(ctx, database, filename):
    'Create PSQL Database and restore SQL file'
    config.update_etc('./etc/server-%s.cfg' % socket.gethostname())
    uri = config.get('database', 'uri')

    logger.info("Restore PSQL database: " + t.green(database))

    if not os.path.isfile(filename):
        logger.error(t.red('ERROR:')+' File NOT found ' + filename)
        return

    logger.info("Create database...")

    command = 'createdb %(database)s -U %(username)s' % {
        'database': database,
        'username': parse_uri(uri).username,
        }
    run(command)

    logger.info("Load database...")

    command = 'psql -d %(database)s -U %(username)s < ./%(filename)s' % {
        'database': database,
        'username': parse_uri(uri).username,
        'filename': filename,
        }
    run(command)

@task()
def dropdb(database):
    'Drop PSQL Database'
    config.update_etc('./etc/server-%s.cfg' % socket.gethostname())
    uri = config.get('database', 'uri')

    logger.info("Drop PSQL database: " + t.green(database))

    command = 'dropdb %(database)s -U %(username)s' % {
        'database': database,
        'username': parse_uri(uri).username,
        }
    run(command)

# Add Invoke Collections
GalCollection = Collection()
GalCollection.add_task(create)
GalCollection.add_task(install)
GalCollection.add_task(dump)
GalCollection.add_task(restore)
