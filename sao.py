#This file is part of tryton-task. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import logging
import os
from invoke import Collection, task
from blessings import Terminal

t = Terminal()
logger = logging.getLogger(__name__)

__all__ = ['install', 'grunt']

@task
def install(ctx):
    'Install SAO'
    os.chdir('public_data/sao')
    os.system('npm install')
    os.system('bower install')

    logger.info(t.bold('Done'))

@task
def grunt(ctx):
    'Grunt SAO'
    os.chdir('public_data/sao')
    os.system('grunt')

    logger.info(t.bold('Done'))

# Add Invoke Collections
SaoCollection = Collection()
SaoCollection.add_task(install)
SaoCollection.add_task(grunt)
