#This file is part of trytontasks_userdoc. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import os
import glob
import logging
from invoke import Collection, task, run
from blessings import Terminal
from path import Path
from string import Template

t = Terminal()
logger = logging.getLogger(__name__)

def create_symlinks(origin, destination, lang='es', remove=True):
    if remove:
        # Removing existing symlinks
        for link_file in Path(destination).listdir():
            if link_file.islink():
                link_file.remove()

    for module_doc_dir in glob.glob('%s/*/doc/%s' % (origin, lang)):
        module_name = str(Path(module_doc_dir).parent.parent.basename())
        symlink = Path(destination).joinpath(module_name)
        if not symlink.exists():
            Path(destination).relpathto(Path(module_doc_dir)).symlink(symlink)

def make_link(origin, destination):
    directory = os.path.dirname(destination)
    if not os.path.exists(destination):
        Path(directory).relpathto(Path(origin)).symlink(destination)

@task
def install(ctx):
    'Install User DOC'
    run('pip install sphinx')
    run('pip install sphinxcontrib-inheritance')
    run('pip install trydoc --no-dependencies') # force not install proteus from pypi
    #~ run('which sphinx-build')
    run('hg clone https://bitbucket.org/trytonspain/trytond-doc')

    logger.info(t.bold('Done'))

@task
def make(ctx, modules='modules', user_doc_path='trytond-doc',
        source_doc='doc-src', doc_path="doc", lang="es", project_name=None,
        version=None, copyright=None):
    'Make User DOC'
    if not os.path.exists(modules):
        logger.info(t.bold('Not found modules dir'))
        exit()
    if not os.path.exists(user_doc_path):
        logger.info(t.bold('Clone https://bitbucket.org/trytonspain/trytond-doc'))
        exit()
    if not os.path.exists(source_doc):
        run("mkdir %(source_doc)s" % locals())
    if not os.path.exists(doc_path):
        run("mkdir %(doc_path)s" % locals())

    # create symlinks from modules.
    create_symlinks(modules, source_doc, lang, True)
    # create symlinks from core modeules.
    create_symlinks(user_doc_path, source_doc, lang, False)

    conf_file = '%s/conf.py' % source_doc
    if not os.path.exists(conf_file):
        template = '%s/conf.py.template' % user_doc_path
        with open(template, 'r') as f:
            tpl_config = f.read()

        vals = {
            'PROJECT': project_name or 'Tryton Doc',
            'COPYRIGHT': copyright or 'Tryton ERP',
            'VERSION': version or '4.2',
            }
        tpl = Template(tpl_config).substitute(vals)
        with open(conf_file, 'w') as f:
            f.write(tpl)

    # create symlink for index
    index = os.path.join(user_doc_path, 'index.rst')
    link = os.path.join(source_doc, 'index.rst')
    make_link(index, link)

    logger.info(t.bold('Done'))

@task
def build(ctx, source_doc='doc-src', doc_path="doc", buildername='html'):
    'Build User DOC (html, singlehtml...)'
    dbname = os.environ.get('DB_NAME')
    trytond_config = os.environ.get('TRYTOND_CONFIG')
    if not dbname or not trytond_config:
        logger.info(t.red('Missign DB_NAME or TRYTOND_CONFIG'))
        logger.info(t.green('export DB_NAME=databasename'))
        logger.info(t.green('export TRYTOND_CONFIG=trytond.cfg'))
        exit()

    logger.info('Database: ' + t.bold(dbname))
    logger.info('Config file: ' + t.bold(trytond_config))

    # Sphinx Build options: http://www.sphinx-doc.org/en/stable/invocation.html
    cmd = 'sphinx-build -b %s %s %s' % (buildername, source_doc, doc_path)
    run(cmd)

    logger.info(t.bold('Done'))

# Add Invoke Collections
UserDocCollection = Collection('doc')
UserDocCollection.add_task(install)
UserDocCollection.add_task(make)
UserDocCollection.add_task(build)
