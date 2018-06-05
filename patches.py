#!/usr/bin/env python
import os
import logging
from invoke import task, Collection, run
from blessings import Terminal
from quilt.push import Push
from quilt.pop import Pop
from quilt.db import PatchSeries
from quilt.error import AllPatchesApplied, QuiltError, UnknownPatch

patches_dir = "patches"
pc_dir = ".pc"
series_file = 'series'

t = Terminal()
logger = logging.getLogger(__name__)

@task()
def applied(ctx, expect_empty=False):
    '''Applied patches (quilt)'''
    logger.info(t.bold('Patches Applied'))
    res = run('quilt applied',  warn=True)
    patches = res.stdout.split('\n')
    for patch in patches:
        if expect_empty:
            logger.info(t.red(patch))
            return False
    return True

@task()
def unapplied(ctx):
    '''Unapplied patches (quilt)'''
    logger.info(t.bold('Patches Not Applied'))
    res = run('quilt unapplied', hide='stdout', warn=True)
    patches = res.stdout.split('\n')
    for patch in patches:
        logger.info(t.red(patch))

def _pop(force=False):
    pop = Pop(os.getcwd(), pc_dir)
    try:
        pop.unapply_all(force)
    except QuiltError, e:
        logger.info(t.red('KO: Error applying patch:' + str(e)))
        return -1
    except UnknownPatch, e:
        logger.info(t.red('KO: Error applying patch:' + str(e)))
        return -1
    logger.info(t.green('OK: All Patches removed'))
    return 0

@task()
def pop(ctx, force=False):
    '''Pop patches (quilt)'''
    _pop(force)

def _push(force=False, quiet=True):
    push = Push(os.getcwd(), pc_dir, patches_dir)
    try:
        push.apply_all(force, quiet)
    except AllPatchesApplied:
        logger.info(t.green('OK: Patches already Applied'))
        return 0
    except QuiltError, e:
        logger.info(t.red('KO: Error applying patch:' + str(e)))
        return -1
    except UnknownPatch, e:
        logger.info(t.red('KO: Error applying patch:' + str(e)))
        return -1
    logger.info(t.green('OK: All Patches Applied'))
    return 0

@task()
def push(ctx, force=False, quiet=True):
    '''Push patches (quilt)'''
    _push(force=False, quiet=True)

QuiltCollection = Collection('quilt')
QuiltCollection.add_task(pop)
QuiltCollection.add_task(applied)
QuiltCollection.add_task(unapplied)
QuiltCollection.add_task(push)
