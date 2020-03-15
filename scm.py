#This file is part of trytontasks_scm. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from invoke import run
import hgapi
import git
import logging
import os
from blessings import Terminal

t = Terminal()
logger = logging.getLogger(__name__)

def get_url(url, master=False):
    files = ['~/.ssh/id_dsa', '~/.ssh/id_rsa']
    exists = False
    for f in files:
        if os.path.exists(os.path.expanduser(f)):
            exists = True
            break
    if not exists:
        if url.startswith('ssh'):
            url = 'https' + url[3:]
    if not master:
        if 'hg.tryton.org' in url:
            url = url.replace('hg.tryton.org', 'hg.zikzakmedia.com')
            url = url.replace('modules/', '')
    return url

def check_revision(client, module, revision, branch):
    if client.revision(revision).branch != branch:
        logger.info(t.bold_red('[' + module + ']'))
        logger.info("Invalid revision '%s': it isn't in branch '%s'"
            % (revision, branch))
        return -1
    return 0

def hg_clone(url, path, branch="default", master=False, revision=None):
    url = get_url(url, master)
    extended_args = ['--pull']
    if revision or branch:
        extended_args.append('-u')
        extended_args.append(revision or branch)
    try:
        client = hgapi.hg_clone(url, path, *extended_args)
        if revision:
            check_revision(client, path, revision, branch)
    except hgapi.HgException as e:
        logger.info(t.bold_red('[' + path + ']'))
        logger.info("Error running %s: %s" % (e.exit_code, str(e)))
        return -1
    except:
        return -1

    if revision:
        logger.info("Repo " + t.bold(path) + t.green(" Updated") + \
            " to revision: " + revision)
    else:
        logger.info("Repo " + t.bold(path) + t.green(" Updated") + \
            " and branch: " + branch)

def hg_update(path):
    try:
        repo = hgapi.Repo(path)
        repo.hg_pull()
        revision = repo.hg_branch()
        repo.hg_update(revision)
    except hgapi.HgException as e:
        logger.info(t.bold_red('[' + path + ']'))
        logger.info("Error running %s: %s" % (e.exit_code, str(e)))
        return -1
    except:
        return -1

    logger.info("Repo " + t.bold(path) + t.green(" Updated"))

def git_clone(url, path, branch="master", revision="master"):
    git.Repo.clone_from(url, path, branch=branch)
    print("Repo " + t.bold(path) + t.green(" Cloned"))
    return 0

def git_update(path):
    path_repo = os.path.join(path)
    if not os.path.exists(path_repo):
        if ignore_missing:
            return 0
        logger.info("Missing repositori: %s" % path_repo)
        return -1

    cwd = os.getcwd()
    os.chdir(path_repo)

    cmd = ['git', 'pull']
    result = run(' '.join(cmd), warn=True, hide='both')

    if not result.ok:
        logger.info("KO update repositori: %s" % path_repo)
        os.chdir(cwd)
        return -1

    # If git outputs 'Already up-to-date' do not print anything.
    if ('Already up to date' in result.stdout
            or 'Already up-to-date' in result.stdout):
        os.chdir(cwd)
        return 0

    logger.info("Update repositori: %s" % result.stdout)
    os.chdir(cwd)
    return 0
