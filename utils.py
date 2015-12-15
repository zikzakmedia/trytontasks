#This file is part of trytontasks. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import os
from trytontasks_modules import read_config_file

def clean_modules(Servers, Modules):
    'Remove servers sections in cfg modules'
    assert os.path.exists('./config/servers.cfg'), "Not found servers.cfg"

    servers = Servers.sections()
    for server in servers: Modules.remove_section(server)

    # remove base modules. Updated with "hg upull"
    Bases = read_config_file('base.cfg')
    bases = Bases.sections()
    for base in bases: Modules.remove_section(base)

    return Modules
