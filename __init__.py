#This file is part of tryton-task. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from invoke import Collection

# import here your tryton tasks projects
from .modules import ModulesCollection
from .sao import SaoCollection
from .server import ServerCollection

ns = Collection()
ns.add_collection(ModulesCollection, 'modules')
ns.add_collection(SaoCollection, 'sao')
ns.add_collection(ServerCollection, 'server')
