#This file is part of tryton-task. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import logging
import sys
from invoke import Collection

# import here your tryton tasks projects
from .modules import ModulesCollection
from .sao import SaoCollection
from .server import ServerCollection
from .patches import QuiltCollection

try:
    from userdoc import UserDocCollection
    required_proteus = True
except:
    required_proteus = False

try:
    from gal import GalCollection
    required_trytond = True
except:
    required_trytond = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

ns = Collection()
ns.add_collection(ModulesCollection)
ns.add_collection(SaoCollection)
ns.add_collection(ServerCollection)
ns.add_collection(QuiltCollection)

if required_proteus:
    ns.add_collection(UserDocCollection)

if required_trytond:
    ns.add_collection(GalCollection)
