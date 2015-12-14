#This file is part of trytontasks. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from invoke import Collection

# import here your tryton tasks projects
import trytontasks_modules
import trytontasks_gal
from .bootstrap import *

ns = Collection()
ns.add_collection(Collection.from_module(trytontasks_modules, name='modules'))
ns.add_collection(Collection.from_module(trytontasks_gal, name='gal'))
ns.add_collection(Collection.from_module(bootstrap, name='zz'))