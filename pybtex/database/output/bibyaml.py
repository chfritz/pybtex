# Copyright 2006 Andrey Golovizin
#
# This file is part of pybtex.
#
# pybtex is free software; you can redistribute it and/or modify
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# pybtex is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pybtex; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
# USA

import yaml
from pybtex.core import Entry
from pybtex.database.output import WriterBase

file_extension = 'bibtexml'
doctype = """<!DOCTYPE bibtex:file PUBLIC
    "-//BibTeXML//DTD XML for BibTeX v1.0//EN"
        "bibtexml.dtd" >
"""
class Writer(WriterBase):
    """Outputs YAML markup"""

    def write(self, bib_data, filename):
        def process_person_roles(entry):
            for role in Entry.valid_roles:
                persons = getattr(entry, role + 's')
                if persons:
                    yield role, list(process_persons(persons))

        def process_person(person):
            for type in ('first', 'middle', 'prelast', 'last', 'lineage'):
                name = person.get_part_as_text(type)
                if name:
                    yield type, name

        def process_persons(persons):
            for person in persons:
                yield dict(process_person(person))
                
        def process_entries(bib_data):
            for key, entry in bib_data.iteritems():
                fields = dict(entry.fields)
                fields['type'] = entry.type
                fields.update(process_person_roles(entry))
                yield key, fields

        data = {'data': dict(process_entries(bib_data))}
        f = open(filename, 'w')
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, indent=4)
        f.close()