#This file is part of trytontasks_scm. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import hgapi
import os
from blessings import Terminal

t = Terminal()

def get_url(url):
    files = ['~/.ssh/id_dsa', '~/.ssh/id_rsa']
    exists = False
    for f in files:
        if os.path.exists(os.path.expanduser(f)):
            exists = True
            break
    if not exists:
        if url.startswith('ssh'):
            url = 'https' + url[3:]
    return url

def check_revision(client, module, revision, branch):
    if client.revision(revision).branch != branch:
        print t.bold_red('[' + module + ']')
        print ("Invalid revision '%s': it isn't in branch '%s'"
            % (revision, branch))
        return -1
    return 0

def hg_clone(url, path, branch="default", revision=None):
    url = get_url(url)
    extended_args = ['--pull']
    if revision or branch:
        extended_args.append('-u')
        extended_args.append(revision or branch)
    try:
        client = hgapi.hg_clone(url, path, *extended_args)
        if revision:
            check_revision(client, path, revision, branch)
    except hgapi.HgException, e:
        print t.bold_red('[' + path + ']')
        print "Error running %s: %s" % (e.exit_code, str(e))
        return -1
    except:
        return -1

    if revision:
        print "Repo " + t.bold(path) + t.green(" Updated") + \
            " to revision: " + revision
    else:
        print "Repo " + t.bold(path) + t.green(" Updated") + \
            " and branch: " + branch
