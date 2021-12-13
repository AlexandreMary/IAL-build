#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Make or populate a pack from Git.
"""
import os
import argparse
import sys

# Automatically set the python path
repo_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(repo_path, 'src'))

from ial_build.algos import parse_programs, IALgitref2pack
from ial_build.pygmkpack import GmkpackTool
from ial_build.config import DEFAULT_IAL_REPO

DEFAULT_COMPILER_FLAG = os.environ.get('GMK_OPT', '2y')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make or populate a pack from Git.')
    parser.add_argument('git_ref',
                        help='Git ref: branch or tag.')
    parser.add_argument('-l', '--compiler_label',
                        default=GmkpackTool.get_compiler_label(),
                        help='Compiler label.')
    parser.add_argument('-o', '--compiler_flag',
                        help='Compiler flag.',
                        default=DEFAULT_COMPILER_FLAG)
    parser.add_argument('-t', '--packtype',
                        help='Type of pack (default: incr).',
                        default='incr',
                        choices=['incr', 'main'])
    parser.add_argument('-e', '--preexisting_pack',
                        action='store_true',
                        help='Assume the pack already preexists.',
                        default=False)
    parser.add_argument('-c', '--clean_if_preexisting',
                        action='store_true',
                        help='Call cleanpack.',
                        default=False)
    parser.add_argument('-r', '--repository',
                        help='Location of the Git repository in which to populate branch (defaults to: {}).'.format(DEFAULT_IAL_REPO),
                        default=DEFAULT_IAL_REPO)
    parser.add_argument('-p', '--programs',
                        help="Programs which ics_{p} script to be generated, e.g. 'masterodb' or 'masterodb,bator'",
                        default='')
    parser.add_argument('--homepack',
                        default=None,
                        help='To specify a home directory for packs (defaults to $HOMEPACK or $HOME/pack)')
    parser.add_argument('-f', '--rootpack',
                        help="Home of root packs to start from, for incremental packs. Cf. Gmkpack's $ROOTPACK",
                        default=None)
    args = parser.parse_args()
    pack = IALgitref2pack(args.git_ref,
                          args.repository,
                          pack_type=args.packtype,
                          preexisting_pack=args.preexisting_pack,
                          clean_if_preexisting=args.clean_if_preexisting,
                          compiler_label=args.compiler_label,
                          compiler_flag=args.compiler_flag,
                          homepack=args.homepack,
                          rootpack=args.rootpack)
    if args.programs != '':
        for p in parse_programs(args.programs):
            pack.ics_build_for(p, GMK_THREADS=4)
