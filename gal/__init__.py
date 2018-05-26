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
from trytond.config import config, parse_uri

t = Terminal()
logger = logging.getLogger(__name__)
TODAY = datetime.date.today()

TRYTOND_CONFIG = os.environ.get('TRYTOND_CONFIG',
    './etc/server-%s.cfg' % socket.gethostname())

@task()
def create(ctx, database):
    'Create trytond database and langs. The DB must created with createdb psql.'
    logger.info('Create DB %s' % database)

    command = 'trytond/bin/trytond-admin -v -c %(config)s --all -d %(database)s -l es' % {
        'config': TRYTOND_CONFIG,
        'database': database,
        }
    run(command)

@task()
def install(ctx, database, modules=None):
    'Install modules'

    command = './tasks/gal/activate.py -d %(database)s' % {
        'database': database,
        }
    if modules:
        command += ' -m %s' % modules
    run(command)

    command = 'trytond/bin/trytond-admin -v -c %(config)s --all -d %(database)s' % {
        'config': TRYTOND_CONFIG,
        'database': database,
        }
    run(command)

    command = './tasks/gal/activate_config.py -d %(database)s' % {
        'database': database,
        }
    if modules:
        command += ' -m %s' % modules
    run(command)

@task()
def demo(ctx, database, modules=None):
    'Demo modules'

    command = './tasks/gal/demo.py -d %(database)s' % {
        'database': database,
        }
    if modules:
        command += ' -m %s' % modules
    run(command)

@task()
def dump(ctx, database):
    'Dump PSQL Database to SQL file'
    config.update_etc(TRYTOND_CONFIG)
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
    config.update_etc(TRYTOND_CONFIG)
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
    config.update_etc(TRYTOND_CONFIG)
    uri = config.get('database', 'uri')

    logger.info("Drop PSQL database: " + t.green(database))

    command = 'dropdb %(database)s -U %(username)s' % {
        'database': database,
        'username': parse_uri(uri).username,
        }
    run(command)

# Add Invoke Collections
GalCollection = Collection('gal')
GalCollection.add_task(create)
GalCollection.add_task(install)
GalCollection.add_task(demo)
GalCollection.add_task(dump)
GalCollection.add_task(restore)
