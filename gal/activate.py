#!/usr/bin/env python
# encoding: utf-8
import optparse
import socket
import sys
import os
import logging
from decimal import Decimal
from blessings import Terminal
from .utils import get_modules

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
    'language': 'es',
}

logger.info('Start install modules')

with Transaction().start(dbname, 1, context=context):
    Lang = pool.get('ir.lang')
    User = pool.get('res.user')
    Module = pool.get('ir.module')
    ModuleActivateUpgrade = pool.get('ir.module.activate_upgrade', type='wizard')

    # Locale
    ca, es = Lang.search([
            ('code', 'in', ['ca', 'es']),
            ])
    Lang.write([ca, es], {'translatable': True})

    # Set lang in admin user
    admin, = User.search([
            ('login', '=', 'admin'),
            ], limit=1)
    User.write([admin], {'language': es})

    # install
    if options.modules:
        modules = options.modules.split(',')
    else:
        modules = get_modules().get('to_activated', [])
    logger.info(t.green('Modules to install: %s' % ', '.join(modules)))

    modules = Module.search([
            ('name', 'in', modules),
            ('state', '=', 'not activated'),
            ])
    Module.write(modules, {'state': 'to activate'})

    # session_id, _, _ = ModuleActivateUpgrade.create()
    # load = ModuleActivateUpgrade(session_id)
    # print "session_id"
    # print session_id
    # load.transition_upgrade()

    Transaction().commit()

logger.info('End install modules')
