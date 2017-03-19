#This file is part of tryton-task. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import os
import sys
import contextlib
import logging
from blessings import Terminal

try:
    from trytond.config import config as CONFIG
    from trytond.transaction import Transaction
except:
    pass

MAX_PROCESSES = 25
t = Terminal()
logger = logging.getLogger(__name__)

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

    try:
        from trytond.config import config as CONFIG
    except ImportError, e:
        logger.error(sys.stderr + "trytond importation error: " + e)

def set_context(database_name, config_file=os.environ.get('TRYTOND_CONFIG')):
    CONFIG.update_etc(config_file)
    if not Transaction().connection:
        return Transaction().start(database_name, 0)
    else:
        return contextlib.nested(Transaction().new_cursor(),
            Transaction().set_user(0),
            Transaction().reset_context())
