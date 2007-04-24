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

"""BibTeX parser"""

import codecs, locale
from pyparsing import *
from pybtex.core import Entry, Person
from pybtex.database.input import ParserBase

month_names = {
    'jan': 'January',
    'feb': 'February',
    'mar': 'March',
    'apr': 'April',
    'may': 'May',
    'jun': 'June',
    'jul': 'July',
    'aug': 'August',
    'sep': 'September',
    'oct': 'October',
    'nov': 'November',
    'dec': 'December'
}

file_extension = 'bib'

def split_name_list(s):
    after_space = False
    brace_level = 0
    name_start = 0
    names = []
    for pos, char in enumerate(s):
        if char.isspace():
            after_space = True
        elif char == '{':
            brace_level += 1
        elif char == '}':
            brace_level -= 1
        elif (brace_level == 0
                and s[pos:pos + 3].lower() == 'and'
                and s[pos + 3:pos+4].isspace()):
            names.append(s[name_start:pos - 1])
            name_start = pos + 4
        after_space = False
    names.append(s[name_start:])
    return names


class Parser(ParserBase):
    def __init__(self, encoding=None, filename=None, **kwargs):
        ParserBase.__init__(self, encoding)
        self.filename = filename

        lbrace = Suppress('{')
        rbrace = Suppress('}')
        def bibtexGroup(s):
            return ((lbrace + s + rbrace) |
                    (Suppress('(') + s + Suppress(')')))

        at = Suppress('@')
        comma = Suppress(',')

        quotedString = Combine(Suppress('"') + ZeroOrMore(CharsNotIn('"\n\r')) + Suppress('"'))
        bracedString = Forward()
        bracedString << Combine(lbrace + ZeroOrMore(CharsNotIn('{}\n\r') | bracedString) + rbrace)
        bibTeXString = quotedString | bracedString

        macro_substitution = Word(alphanums).setParseAction(self.substitute_macro)
        name = Word(alphanums + '!$&*+-./:;<>?[]^_`|').setParseAction(downcaseTokens)
        value = Combine(delimitedList(bibTeXString | Word(nums) | macro_substitution, delim='#'), adjacent=False)

        #fields
        field = Group(name + Suppress('=') + value)
        fields = Dict(delimitedList(field))

        #String (aka macro)
        string_body = bibtexGroup(fields)
        string = at + CaselessLiteral('STRING').suppress() + string_body
        string.setParseAction(self.process_macro)

        #bibliography entry
        entry_header = at + Word(alphas).setParseAction(downcaseTokens)
        entry_key = Word(printables.replace(',', ''))
        if kwargs.get('allow_keyless_entries', False):
            entry_body = bibtexGroup(Optional(entry_key + comma, None) + Group(fields))
        else:
            entry_body = bibtexGroup(entry_key + comma + Group(fields))
        entry = entry_header + entry_body
        entry.setParseAction(self.process_entry)

        self.BibTeX_entry = string | entry

    def set_encoding(self, s):
        self._decode = codecs.getdecoder(s)

    def process_entry(self, s, loc, toks):
        entry = Entry(toks[0].lower())
        fields = {}
        key = toks[1]

        if key is None:
            key = 'unnamed-%i' % self.unnamed_entry_counter
            self.unnamed_entry_counter += 1

        for k, v in toks[2]:
            if k in self.person_fields:
                for name in split_name_list(v):
                    entry.add_person(Person(name), k)
            else:
                entry.fields[k] = v
        return (key, entry)

    def substitute_macro(self, s, loc, toks):
        return self.macros[toks[0].lower()]

    def process_macro(self, s, loc, toks):
        self.macros[toks[0][0].lower()] = toks[0][1]

    def parse_file(self, filename=None, macros=month_names, person_fields=Person.valid_roles):
        """parse BibTeX file and return a tree
        """
        if filename is None:
            filename = self.filename
        self.macros = dict(macros)
        self.person_fields = person_fields
        self.unnamed_entry_counter = 1
        f = codecs.open(filename, encoding=self.encoding)
        s = f.read()
        f.close()
        try:
            return dict(entry[0][0] for entry in self.BibTeX_entry.scanString(s))
        except ParseException, e:
            print "%s: syntax error:" % filename
            print e
            sys.exit(1)
