#This file is part of trytontasks. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import os
from invoke import task, run
from blessings import Terminal
from multiprocessing import Process
from string import Template
from trytontasks_modules import read_config_file
from trytontasks_scm import hg_clone

MAX_PROCESSES = 25
t = Terminal()

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

    Config = read_config_file()
    modules = Config.sections()
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
def install(config=None, module=None, mode=None):
    'Install Tryton modules (mode dev or production)'
    Config = read_config_file(config)
    modules = Config.sections()
    modules.sort()

    if module:
        easy_install = False
        if not module in modules:
            return
        modules = [module]
    else:
        easy_install = True

    def install_repo(url, name, branch='default'):
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
    for module in modules:
        repo = Config.get(module, 'repo')
        url = Config.get(module, 'url')
        path = Config.get(module, 'path')
        branch = Config.get(module, 'branch')

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
        else: # install mode
            if module == 'sao':
                repo_path = os.path.join(path, module)
                if os.path.exists(repo_path):
                    continue
                hg_clone(url, repo_path, branch)
                continue

            repo_path = os.path.join('./src', module)
            if os.path.exists(repo_path):
                continue

            func = install_repo
            print "Adding Module " + t.bold(module) + " to install list"
            p = Process(target=func, args=(url, module, branch))
            p.start()
            processes.append(p)

    if processes:
        wait_processes(processes)

    if easy_install:
        print t.red("Remember regenerate easy-install.pth")
