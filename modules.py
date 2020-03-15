#This file is part of tryton-task. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import configparser
import logging
import os
import hgapi
import git
import yaml
from invoke import Collection, task
from blessings import Terminal
from multiprocessing import Process
from sql import Table
from .scm import hg_clone, hg_update, git_clone, git_update
from .tools import wait_processes, set_context
from . import patches

try:
    from trytond.transaction import Transaction
except:
    pass

t = Terminal()
logger = logging.getLogger(__name__)
MAX_PROCESSES = 25

__all__ = ['info', 'clone', 'branches']


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = "\033[1m"

def read_config_file(config_file=None, type='repos', unstable=True):
    assert type in ('repos', 'servers', 'patches', 'all'), "Invalid 'type' param"

    Config = configparser.ConfigParser()
    if config_file is not None:
        Config.readfp(open('./config/'+config_file))
    else:
        for r, d, f in os.walk("./config"):
            for files in f:
                if not files.endswith(".cfg"):
                    continue
                if not unstable and files.endswith("-unstable.cfg"):
                    continue
                if 'templates' in r:
                    continue
                Config.readfp(open(os.path.join(r, files)))

    if type == 'all':
        return Config
    for section in Config.sections():
        is_patch = (Config.has_option(section, 'patch')
                and Config.getboolean(section, 'patch'))
        is_server = (Config.has_option(section, 'server')
                and Config.get(section, 'server'))
        if type == 'repos' and (is_patch or is_server):
            Config.remove_section(section)
        elif type == 'patches' and not is_patch:
            Config.remove_section(section)
        elif type == 'servers' and not is_server:
            Config.remove_section(section)
    return Config

@task
def info(ctx, config=None):
    'Info config modules'
    Config = read_config_file(config)
    modules = Config.sections()
    modules.sort()

    total = len(modules)
    logger.info(t.bold(str(total) + ' modules'))

    for module in modules:
        message = t.green(module)+' %s %s %s %s' % (
            Config.get(module, 'repo'),
            Config.get(module, 'url'),
            Config.get(module, 'path'),
            Config.get(module, 'branch'),
            )
        print(message)

def _hg_branches(module, path, config_branch=None):
    client = hgapi.Repo(path)
    branches = client.get_branch_names()
    active = client.hg_branch()

    b = []
    branches.sort()
    branches.reverse()
    for branch in branches:
        br = branch

        if branch == active:
            br = "*" + br

        if branch == config_branch:
            br = "[" + br + "]"

        b.append(br)

    msg = str.ljust(module, 40, ' ') + "\t".join(b)

    if "[*" in msg:
        msg = bcolors.OKGREEN + msg + bcolors.ENDC
    elif "\t[" in msg or '\t*' in msg:
        msg = bcolors.FAIL + msg + bcolors.ENDC
    else:
        msg = bcolors.WARN + msg + bcolors.ENDC

    logger.info(msg)

def _git_branches(module, path, config_branch=None):
    repo = git.Repo(path)
    branches = repo.git.branch('-a')
    branches = [x.replace('remotes/origin/','').replace('*','').strip()
        for x in branches.split('\n') if 'HEAD' not in x]
    active = branches[0]
    b = []
    branches = list(set(branches))
    branches.sort()
    branches.reverse()
    for branch in branches:
        br = branch
        if branch == active:
            br = "*" + br
        if branch == config_branch:
            br = "[" + br + "]"
        b.append(br)

    msg = str.ljust(module, 40, ' ') + "\t".join(b)

    if "[*" in msg:
        msg = bcolors.OKGREEN + msg + bcolors.ENDC
    elif "\t[" in msg or '\t*' in msg:
        msg = bcolors.FAIL + msg + bcolors.ENDC
    else:
        msg = bcolors.WARN + msg + bcolors.ENDC

    logger.info(msg)

@task(help={
    'config': 'Configuration file: config.cfg',
    'branch': 'Repo branch. Default is "default"',
    'master': 'If not is true, source repo is from hg.zikzakmedia.com'
    })
def clone(ctx, config=None, branch=None, master=False):
    '''Clone trytond modules'''
    Modules = read_config_file(config)

    modules = Modules.sections()
    modules.sort()

    processes = []
    for module in modules:
        repo = Modules.get(module, 'repo')
        url = Modules.get(module, 'url')
        path = Modules.get(module, 'path')
        mod_branch = branch or Modules.get(module, 'branch')

        repo_path = os.path.join(path, module)
        if os.path.exists(repo_path):
            continue

        if not os.path.exists('./trytond') and config != 'base.cfg':
            logger.info(t.bold_red('Before clone all modules, please clone base.cfg modules'))
            return

        logger.info( "Adding Module " + t.bold(module) + " to clone")

        func = hg_clone if repo == 'hg' else git_clone
        p = Process(target=func, args=(url, repo_path, mod_branch, master))
        p.start()
        processes.append(p)

    if processes:
        wait_processes(processes)

@task
def update(ctx, config=None, module=None):
    '''Update trytond modules'''
    Modules = read_config_file(config)

    modules = Modules.sections()
    modules.sort()

    if module:
        if module in modules:
            modules = [module]
        else:
            logger.error( "Not found " + t.bold(module))
            return

    processes = []
    for module in modules:
        repo = Modules.get(module, 'repo')
        path = Modules.get(module, 'path')

        repo_path = os.path.join(path, module)
        if not os.path.exists(repo_path):
            continue

        logger.info( "Adding Module " + t.bold(module) + " to update")

        func = hg_update if repo == 'hg' else git_update
        p = Process(target=func, args=(repo_path,))
        p.start()
        processes.append(p)

    if processes:
        wait_processes(processes)

@task
def branches(ctx, config=None, module=None):
    '''Show info module branches'''
    Modules = read_config_file(config)

    modules = Modules.sections()
    modules.sort()

    if module:
        modules = [module] if (module and module in modules) else None

    for module in modules:
        repo = Modules.get(module, 'repo')
        url = Modules.get(module, 'url')
        path = Modules.get(module, 'path')
        branch = Modules.get(module, 'branch')

        repo_path = os.path.join(path, module)

        if repo == 'hg':
            _hg_branches(module, repo_path, branch)
        else:
            _git_branches(module, repo_path, branch)

@task
def forgotten(ctx, database, config_file=os.environ.get('TRYTOND_CONFIG')):
    '''Remove modules in ir-modules that not found in cfg config'''

    ir_module = Table('ir_module')

    with set_context(database, config_file):
        cursor = Transaction().connection.cursor()
        cursor.execute(*ir_module.select(ir_module.name, ir_module.state))
        db_module_list = [(r[0], r[1]) for r in cursor.fetchall()]

        Modules = read_config_file()

        modules = Modules.sections()
        modules.append('tests')
        modules.sort()

        to_delete = []
        for module, state in db_module_list:
            if state == 'not activated' and module not in modules:
                to_delete.append(module)

        if to_delete:
            cursor.execute(*ir_module.delete(where=ir_module.name.in_(to_delete)))
            logger.info( "Deleted: " + ', '.join(to_delete))

@task
def tests(ctx, module=None):
    'Tests'
    if module:
        modules = [module]
    else:
        Config = read_config_file()
        modules = Config.sections()
        modules.sort()

    Base = read_config_file('base.cfg')
    bases = Base.sections()

    processes = []
    for module in modules:
        if module in bases:
            continue
        logger.info("Run Module " + t.bold(module) + " to test")
        os.system('python %s/trytond/trytond/tests/run-tests.py -m %s' % (
            os.path.dirname(os.path.realpath(__file__)).replace('/tasks', ''),
            module))

@task
def fetch(ctx):
    '''Fetch env (update trytond, all modules and patches)'''
    logger.info(t.bold('Fetch (patches and update)'))
    logger.info(t.bold('Pop patches...'))
    patches._pop()

    logger.info(t.bold('Pull Update...'))
    update(ctx)

    logger.info(t.bold('Cloning...'))
    clone(ctx)

    logger.info(t.bold('Push patches...'))
    patches._push()

    logger.info(t.bold('Updating requirements...'))
    os.system('pip install -r config/requirements.txt')

    if os.path.isfile('requirements.txt'):
        os.system('pip install -r requirements.txt')

    logger.info(t.bold('Fetched.'))

@task
def missing(ctx):
    '''Missing installed modules (activated_modules.yml)'''
    # activated_modules.yml:
    # activated:
    #   - module name

    if not os.path.isfile('activated_modules.yml'):
        logger.error('Not found activated_modules.yml file')
        return

    # available modules
    Config = read_config_file()
    modules = Config.sections()
    modules.sort()

    # installed modules
    activated = yaml.load(open('activated_modules.yml', 'r').read())
    modules_activated = activated.get('activated')

    # to unistall
    upgrades = yaml.load(open('upgrades/config.yml', 'r').read())
    modules_touninstall = upgrades.get('to_uninstall')
    if os.path.isfile('upgrade.yml'):
        override = yaml.load(open('upgrade.yml', 'r').read())
        modules_touninstall += override.get('to_uninstall', [])

    missing = []
    for module in modules_activated:
        if module in modules_touninstall:
            continue
        if module not in modules:
            missing.append(module)

    logger.info('Missing modules:')
    logger.info(' '.join(missing))

# Add Invoke Collections
ModulesCollection = Collection('modules')
ModulesCollection.add_task(info)
ModulesCollection.add_task(clone)
ModulesCollection.add_task(update)
ModulesCollection.add_task(branches)
ModulesCollection.add_task(forgotten)
ModulesCollection.add_task(tests)
ModulesCollection.add_task(fetch)
ModulesCollection.add_task(missing)
