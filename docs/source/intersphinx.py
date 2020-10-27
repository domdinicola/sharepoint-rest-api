#!/usr/bin/env python
"""# Copyright (c) 2011 individual contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of Django nor the names of its contributors may be used
#        to endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import argparse
import imp
import os
import sys

from sphinx.ext import intersphinx

color_names = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white')
foreground = dict([(color_names[x], '3%s' % x) for x in range(8)])
background = dict([(color_names[x], '4%s' % x) for x in range(8)])
options = {'bold': '1', 'underscore': '4', 'blink': '5', 'reverse': '7', 'conceal': '8'}

WARNING = "{0[yellow]};{2[bold]}".format(foreground, background, options)
ERROR = "{0[red]};{2[bold]}".format(foreground, background, options)
RESET = '\x1b[0m'


def echo(*args):
    assert len(args) >= 2
    style = args[-1]
    if style:
        out = ("\x1b[%sm" % style) + "".join(args[:-1]) + RESET + "\n"
    else:
        out = ("".join(args)) + "\n"
    sys.stdout.write(out)


intersphinx_mapping = {
    'python': ('http://python.readthedocs.org/en/latest/', None),
    'sphinx': ('http://sphinx.readthedocs.org/en/latest/', None),
}


class DummyApp(object):
    srcdir = "."

    def warn(self, msg):
        sys.stderr.write("%s\n" % msg)


def list(args):
    if args.auto:
        pass
    elif args.conf:
        try:
            conf = imp.load_source('conf', args.conf)
            mapping = conf.intersphinx_mapping
            for k, v in mapping.items():
                echo(str(k), str(v), "")
        except IOError as e:
            echo("Unable to load %s" % args.conf, ERROR)
            raise argparse.ArgumentTypeError(e)
    else:
        raise argparse.ArgumentTypeError()


class SphinxPage(object):
    header = r""" .. _interphinx:

=====================
Intersphinx Reference
=====================

Here the list of objects available for this documentation.
To use it add an entry to your ``intersphinx_mapping``.

.. code-block:: python

    intersphinx_mapping = {{
            '{0}': ('http://readthedocs.org/{0}/latest/', None),
            ...
    }}

.. contents::
    :local:
    :depth: 1

"""

    def __init__(self, name, mode, app=''):
        self.file = open(name, mode)
        self.app = str(app)

    def __enter__(self):
        self.writeln(self.header.format(self.app))
        return self

    def __exit__(self, *args):
        self.file.close()

    def writeln(self, *lines):
        for line in lines:
            self.file.write("%s\n" % line)

    def title(self, text):
        sign = "=" * len(text)
        self.writeln(sign, text, sign, "")

    def section(self, text):
        sign = "=" * len(text)
        self.writeln(text, sign, "")

    def subsection(self, text):
        sign = "-" * len(text)
        self.writeln(text, sign, "")


def get_inventory(args):
    app = DummyApp()
    inventory = intersphinx.fetch_inventory(app, "", args.uri)
    if args.dump:
        dump_inventory(inventory)
    if args.create_intersphinx_reference:
        with SphinxPage(args.create_intersphinx_reference, "w", app=args.project) as f:
            sections = sorted(inventory.keys())
            for k in sections:
                term_name = k.split(':')[1]
                term = {'attribute': 'attr',
                        'function': 'func'}.get(term_name, term_name)
                section = inventory[k]
                f.section(term)
                if term == 'label':
                    pattern_as = "``:ref:{1[0]}:{2}``"
                    pattern_test = ":ref:`{2}`"
                else:
                    pattern_as = "``:{0}:{1[0]}:{2}``"
                    pattern_test = ":{0}:`{2}`"

                entries = sorted(section, key=lambda key: section[key])
                for name in entries:
                    values = section[name]
                    access_as = pattern_as.format(term, values, name)
                    access_test = pattern_test.format(term, values, name)

                    f.writeln("    * {0} : '{1}' ({2})".format(name, access_as, access_test))
                f.writeln("", "")
    return "Success"


def dump_inventory(inventory):
    for k in inventory.keys():
        print("Type: %s" % k)
        for name, value in inventory[k].items():
            print("  %s -> '%s'" % (name, value[2]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get human readable intersphinx inventory')
    subparsers = parser.add_subparsers(help='sub-command help')

    parser_get = subparsers.add_parser('get', help='retrieve a Sphinx object inventory from URI')
    parser_get.add_argument('uri', metavar='URI',
                            help='base url to `objects.inv` to parse. ie. http://python.readthedocs.org/en/latest/')

    parser_get.add_argument('--dump', action='store_true',
                            help='dump fetched inventory')

    parser_get.add_argument('-i', '--create-intersphinx-reference', metavar='FILENAME',
                            help='dump fetched inventory to a page')

    parser_get.add_argument('-p', '--project', metavar='project',
                            help='project name')

    parser_get.set_defaults(func=get_inventory)

    parser_list = subparsers.add_parser('list', help='list all mapped URI set in the conf.py')
    parser_list.add_argument('conf', nargs='?', default=None,
                             help='Sphinx conf.py file to read `intersphinx_mapping`')
    parser_list.add_argument('--auto', action='store_true',
                             help='Sphinx cof file to read `intersphinx_mapping`')
    parser_list.add_argument('--dir', default=os.getcwd(),
                             help='directory to scan for sphinx conf.py')

    parser_list.set_defaults(func=list)

    args = parser.parse_args()
    try:
        print(args.func(args))
    except argparse.ArgumentTypeError:
        print(parser.format_help())
