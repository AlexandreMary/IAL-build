#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Make or populate a pack from Git.
"""
import os
import argparse

from ia4h_scm.algos import IA4H_gitref_to_incrpack, IA4H_gitref_to_main_pack
from ia4h_scm.config import DEFAULT_IA4H_REPO

DEFAULT_COMPILER_FLAG = os.environ.get('GMK_OPT', '2y')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make or populate a pack from Git.')
    parser.add_argument('git_ref',
                        help='Git ref: branch or tag.')
    parser.add_argument('-l', '--compiler_label',
                        required=True,
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
                        help='Location of the Git repository in which to populate branch (defaults to: {}).'.format(DEFAULT_IA4H_REPO),
                        default=DEFAULT_IA4H_REPO)
    parser.add_argument('--packname',
                        help='Force pack name (disadvised, and ignored for main packs).',
                        default='__guess__')
    parser.add_argument('--populate_filter_file',
                        help='Filter file (list of files to be filtered) for populate time (defaults from within ia4h_scm package).',
                        default='__inconfig__')
    parser.add_argument('--link_filter_file',
                        help='Filter file (list of files to be filtered) for link time (defaults from within ia4h_scm package).',
                        default='__inconfig__')
    parser.add_argument('--homepack',
                        default=None,
                        help='To specify a home directory for packs (defaults to $HOMEPACK or $HOME/pack)')
    parser.add_argument('-f', '--rootpack',
                        help="Home of root packs to start from, for incremental packs. Cf. Gmkpack's $ROOTPACK",
                        default=None)
    args = parser.parse_args()
    
    assert args.compiler_label not in ('', None), "You must provide a compiler label (option -l or $GMKFILE)."
    if args.packtype == 'incr':
        IA4H_gitref_to_incrpack(args.repository,
                                args.git_ref,
                                args.compiler_label,
                                compiler_flag=args.compiler_flag,
                                packname=args.packname,
                                preexisting_pack=args.preexisting_pack,
                                clean_if_preexisting=args.clean_if_preexisting,
                                homepack=args.homepack,
                                rootpack=args.rootpack,
                                silent=False,
                                ask_confirmation=True)
    else:
        IA4H_gitref_to_main_pack(args.repository,
                                 args.git_ref,
                                 args.compiler_label,
                                 compiler_flag=args.compiler_flag,
                                 homepack=args.homepack,
                                 populate_filter_file=args.populate_filter_file,
                                 link_filter_file=args.link_filter_file,
                                 silent=False,
                                 ask_confirmation=True)
