#This file is part of tryton-task. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from invoke import Collection, task
from blessings import Terminal
from genshi.template import TemplateLoader
from genshi.template.text import NewTextTemplate
import socket
import choice
import crypt
import logging
import random
import string
import os

TEMPLATE_DIR = './config/templates'
t = Terminal()
logger = logging.getLogger(__name__)

if os.path.exists(TEMPLATE_DIR):
    loader = TemplateLoader(TEMPLATE_DIR, auto_reload=True)

__all__ = ['configuration']

@task
def configuration(ctx, name=None):
    'Generate configuration files'
    if not os.path.exists(TEMPLATE_DIR):
        return
    if not name:
        name = socket.gethostname()

    vals = {}
    vals['name'] = name
    port = choice.Input('Port (8000)').ask() or 8000
    nginx = choice.Binary('Nginx', False).ask()
    if nginx:
        vals['nginx'] = nginx
        vals['wsgi'] = str(int(port) + 1) # 8001 
        port = str(int(port) + 2) # 8002
    vals['port'] = port
    vals['path'] = os.path.dirname(__file__).replace('tasks', '')
    vals['dbuser'] = choice.Input('DB User').ask()
    vals['dbpwd'] = choice.Input('DB Password').ask()
    vals['dbname'] = choice.Input('DB Name').ask()
    vals['emailuser'] = choice.Input('Email User').ask()
    vals['emailpwd'] = choice.Input('Email Password').ask()
    vals['emailuri'] = choice.Input('Email URI').ask()
    vals['jasper'] = choice.Input('Port Jasper (8090)').ask()
    superpwd = choice.Input('Super Password', str).ask()
    vals['superpwd'] = crypt.crypt(superpwd, "".join(random.sample(string.ascii_letters + string.digits, 8)))

    tmpl = loader.load('trytond.conf', cls=NewTextTemplate)
    trytond = tmpl.generate(**vals).render()
    with open('etc/server-%s.cfg' % name, 'w') as f:
        f.write(trytond)

    if nginx:
        tmpl = loader.load('nginx.tpl', cls=NewTextTemplate)
        nginx = tmpl.generate(**vals).render()
        with open('etc/nginx-%s' % name, 'w') as f:
            f.write(nginx)

        tmpl = loader.load('gunicorn.tpl', cls=NewTextTemplate)
        gunicorn = tmpl.generate(**vals).render()
        with open('etc/gunicorn-%s.py' % name, 'w') as f:
            f.write(gunicorn)

        tmpl = loader.load('supervisor.conf', cls=NewTextTemplate)
        supervisor = tmpl.generate(**vals).render()
        with open('etc/supervisor-%s.cfg' % name, 'w') as f:
            f.write(supervisor)

        tmpl = loader.load('supervisor_trytond-wsgi.conf', cls=NewTextTemplate)
        supervisor_trytond = tmpl.generate(**vals).render()
        with open('etc/supervisor-%s-wsgi.cfg' % name, 'w') as f:
            f.write(supervisor_trytond)

        tmpl = loader.load('supervisor_trytond-trytond.conf', cls=NewTextTemplate)
        supervisor_trytond = tmpl.generate(**vals).render()
        with open('etc/supervisor-%s-trytond.cfg' % name, 'w') as f:
            f.write(supervisor_trytond)

        tmpl = loader.load('supervisor_trytond-cron.conf', cls=NewTextTemplate)
        supervisor_cron = tmpl.generate(**vals).render()
        with open('etc/supervisor-%s-cron.cfg' % name, 'w') as f:
            f.write(supervisor_cron)

        tmpl = loader.load('trytond-logs.conf', cls=NewTextTemplate)
        trytond_logs = tmpl.generate(**vals).render()
        with open('etc/server-%s-logs.cfg' % name, 'w') as f:
            f.write(trytond_logs)

    logger.info(t.bold('Created configuration files'))

# Add Invoke Collections
ServerCollection = Collection()
ServerCollection.add_task(configuration)
