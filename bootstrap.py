#This file is part of trytontasks. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import os
from invoke import task, run
from blessings import Terminal
from multiprocessing import Process
from string import Template
from trytontasks_modules import read_config_file
from trytontasks_scm import hg_clone
import logging
logging.basicConfig()

try:
    from cookiecutter.main import cookiecutter as cookiecutter_main
    cookiecutter = True
except:
    cookiecutter = False

MAX_PROCESSES = 25
t = Terminal()

if os.path.exists('./config') and not os.path.exists('./config/servers.cfg'):
    open('./config/servers.cfg', 'a').close()

def wait_processes(processes, maximum=MAX_PROCESSES, exit_code=None):
    i = 0
    while len(processes) > maximum:
        if i >= len(processes):
            i = 0
        p = processes[i]
        p.join(0.1)
        if p.is_alive():
            i += 1
        else:
            if exit_code is not None:
                exit_code.append(processes[i].exitcode)
            del processes[i]

@task
def easy_install():
    'Regenerate easy-install.pth'
    Servers = read_config_file('servers.cfg', type='servers')
    Modules = read_config_file()

    modules = Modules.sections()
    modules.sort()

    paths = []
    for module in modules:
        if module == 'sao':
            continue
        paths.append('%s/src/%s' % (os.getcwd(), module.replace('_','-')))

    tpl_ = './tasks/easy-install.pth.template'
    with open(tpl_, 'r') as f:
        tpl_base = f.read()

    vals = {'MODULES': '\n'.join(paths)}
    tpl = Template(tpl_base).substitute(vals)

    file_ = './lib/python2.7/site-packages/easy-install.pth'
    if not os.path.exists(file_):
        print "Not found " + t.bold(file_) 
        return
    with open(file_, 'w') as f:
        f.write(tpl) 

@task
def install(config=None, module=None, mode='dev'):
    'Install Tryton modules (mode dev or production)'
    Servers = read_config_file('servers.cfg', type='servers')
    Modules = read_config_file(config)

    modules = Modules.sections()
    modules.sort()

    if module:
        if not module in modules:
            return
        modules = [module]

    def _install_repo(url, name, branch='default'):
        command = 'pip install -e hg+%s/@%s#egg=%s --no-dependencies' % (url, branch, name)

        try:
            run(command)

            nlink = name.split('_')
            if len(nlink)>1:
                run('cd %s;ln -s %s %s' % ('./src/', name.replace('_','-'), name))

            pkg_egg = 'trytond_%s.egg-info' % module
            if os.path.exists('src/%(name)s/trytonzz_%(name)s.egg-info' % {'name': name}):
                pkg_egg = 'trytonzz_%s.egg-info' % module
            if os.path.exists('src/%(name)s/trytonspain_%(name)s.egg-info' % {'name': name}):
                pkg_egg = 'trytonspain_%s.egg-info' % module
            if os.path.exists('src/%(name)s/nantic_%(name)s.egg-info' % {'name': name}):
                pkg_egg = 'nantic_%s.egg-info' % module
            run('cd %s;ln -s %s/PKG-INFO PKG-INFO' % ('./src/'+name, pkg_egg))

            print t.green('Installed')+": "+t.bold(name)
        except:
            print "Error running " + t.bold(name)
            raise

    processes = []
    i = 0
    for module in modules:
        repo = Modules.get(module, 'repo')
        url = Modules.get(module, 'url')
        path = Modules.get(module, 'path')
        branch = Modules.get(module, 'branch')

        if mode == 'dev': # dev mode
            repo_path = os.path.join(path, module)
            if os.path.exists(repo_path):
                continue

            if not os.path.exists('./trytond') and config != 'base.cfg':
                print t.bold_red('First clone base.cfg modules')
                return

            print "Adding Module " + t.bold(module) + " to process dev list"

            func = hg_clone
            p = Process(target=func, args=(url, repo_path, branch))
            p.start()
            processes.append(p)
        else: # install mode # TODO Remove pip install
            if module == 'sao':
                repo_path = os.path.join(path, module)
                if os.path.exists(repo_path):
                    continue
                hg_clone(url, repo_path, branch)
                continue

            repo_path = os.path.join('./src', module)
            if os.path.exists(repo_path):
                continue
            if i < MAX_PROCESSES:
                func = _install_repo
                print "Adding Module " + t.bold(module) + " to install list"
                p = Process(target=func, args=(url, module, branch))
                p.start()
                processes.append(p)
            i += 1

    if processes:
        wait_processes(processes)

    if mode != 'dev':
        print t.red("Remember regenerate easy-install.pth")

@task
def update(server=None, module=None):
    'Update Tryton modules (hg pull update)'
    Servers = read_config_file('servers.cfg', type='servers')
    servers = Servers.sections()
    servers.sort()

    Modules = read_config_file()

    if server == 'zzsaas':
        # remove core modules. Updated with "hg upull"
        Cores = read_config_file('core.cfg')
        cores = Cores.sections()
        for core in cores: Modules.remove_section(core)

    modules = Modules.sections()
    modules.sort()

    if module:
        if not module in modules:
            return
        modules = [module]

    if server:
        if not server in servers:
            return
        servers = [server]

    def _hg_pull_update(hostname, port, path):
        return run("ssh -p %(port)s %(hostname)s 'cd %(path)s;hg pull -u'" % {
                'port': port,
                'hostname': hostname,
                'path': path,
                }, pty=True, warn=True)

    for server in servers:
        hostname, port = Servers.get(server, 'server').split(':')
        for module in modules:
            path = '%s/%s' % (Servers.get(server, 'path_modules'), module)
            if _hg_pull_update(hostname, port, path):
                print "Updated " + t.bold(server) + ": "+t.green(module)

@task
def cookicuter(repo=None):
    'Create projects from project template - cookiecutter'
    if not repo:
        repo = 'https://bitbucket.org/zikzakmedia/cookiecutter-tryton'
    if not cookiecutter:
        print 'cookiecutter %s' % repo
        return

    cookiecutter_main(repo)
