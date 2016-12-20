#This file is part of tryton-task. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import ConfigParser
import os
import hgapi
from invoke import Collection, task
from blessings import Terminal
from multiprocessing import Process
from .scm import hg_clone
from .tools import wait_processes

t = Terminal()
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

    Config = ConfigParser.ConfigParser()
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
    print t.bold(str(total) + ' modules')

    for module in modules:
        print t.green(module)+' %s %s %s %s' % (
            Config.get(module, 'repo'),
            Config.get(module, 'url'),
            Config.get(module, 'path'),
            Config.get(module, 'branch'),
            )

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

    print msg

@task
def clone(ctx, config=None, branch=None):
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
            print t.bold_red('Before clone all modules, please clone base.cfg modules')
            return

        print "Adding Module " + t.bold(module) + " to clone"

        func = hg_clone
        p = Process(target=func, args=(url, repo_path, mod_branch))
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

        _hg_branches(module, repo_path, branch)

# Add Invoke Collections
ModulesCollection = Collection()
ModulesCollection.add_task(info)
ModulesCollection.add_task(clone)
ModulesCollection.add_task(branches)