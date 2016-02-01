#This file is part of trytontasks. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from invoke import Collection
try:
    import proteus as tryproteus
    proteus = True
except:
    proteus = False

# import here your tryton tasks projects
import trytontasks_modules
import trytontasks_sao
from .bootstrap import *
from .bank import *

try:
    import trytontasks_gal
    gal = True
except:
    gal = False

try:
    import trytontasks_userdoc
    userdoc = True
except:
    userdoc = False

try:
    import trytontasks_tests
    tests = True
except:
    tests = False

ns = Collection()
ns.add_collection(Collection.from_module(trytontasks_modules, name='modules'))
ns.add_collection(Collection.from_module(trytontasks_sao, name='sao'))
ns.add_collection(Collection.from_module(bootstrap, name='zz'))
if proteus:
    ns.add_collection(Collection.from_module(bank, name='bank'))
if gal:
    ns.add_collection(Collection.from_module(trytontasks_gal, name='gal'))
if userdoc:
    ns.add_collection(Collection.from_module(trytontasks_userdoc, name='doc'))
if tests:
    ns.add_collection(Collection.from_module(trytontasks_tests, name='tests'))
