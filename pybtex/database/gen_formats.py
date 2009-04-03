#!/usr/bin/env python

"""Generate a bidirectional map between file formats and extensions."""

# XXX should it be in pybtex.plugins?

from os.path import basename
from glob import glob1
from pybtex.plugin import find_plugin

def available_formats():
    for filename in glob1('input', '*.py'):
        if filename != '__init__.py':
            yield filename.replace('.py', '')


def filetypes():
    for format in available_formats():
        plugin = find_plugin('pybtex.database.input', format)
        yield format, plugin.file_extension

def gen_formats():
    extension_for_format = dict(filetypes())
    format_for_extension = dict((value, key)
            for (key, value) in extension_for_format.items())

    output = open('formats.py', 'w')
    output.write('# generated by %s\n' % basename(__file__))
    output.write('# do not edit\n\n')
    output.write('format_for_extension = %r\n\n' % format_for_extension)
    output.write('extension_for_format = %r\n' % extension_for_format)
    output.close()

if __name__ == '__main__':
    gen_formats()