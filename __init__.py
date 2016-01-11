#This file is part of trytontasks. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from invoke import Collection

# import here your tryton tasks projects
import trytontasks_modules
import trytontasks_gal
import trytontasks_sao
from .bootstrap import *

try:
    import trytontasks_userdoc
    userdoc = True
except:
    userdoc = False

ns = Collection()
ns.add_collection(Collection.from_module(trytontasks_modules, name='modules'))
ns.add_collection(Collection.from_module(trytontasks_sao, name='sao'))
ns.add_collection(Collection.from_module(bootstrap, name='zz'))

if userdoc:
    ns.add_collection(Collection.from_module(trytontasks_userdoc, name='doc'))
