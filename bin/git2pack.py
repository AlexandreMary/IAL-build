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

from ial_build.algos import IA4H_gitref_to_incrpack, IA4H_gitref_to_main_pack
from ial_build.config import DEFAULT_IA4H_REPO

DEFAULT_COMPILER_FLAG = os.environ.get('GMK_OPT', '2y')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make or populate a pack from Git.')
    parser.add_argument('git_ref',
                        help='Git ref: branch or tag.')
    parser.add_argument('-l', '--compiler_label',
                        required=True,
                        help='Compiler label.')
    parser.add_argument('--fetch',
                        help='Fetch remote beforehand.',
                        action='store_true',
                        default=False)
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
    parser.add_argument('--start_ref',
                        help='Specify a Git reference, from which increment of modifications starts. Use with precaution !.',
                        default=None)
    parser.add_argument('-c', '--clean_if_preexisting',
                        action='store_true',
                        help='Call cleanpack.',
                        default=False)
    parser.add_argument('-r', '--repository',
                        help='Location of the Git repository in which to populate branch (defaults to: {}).'.format(DEFAULT_IA4H_REPO),
                        default=DEFAULT_IA4H_REPO)
    name = parser.add_mutually_exclusive_group()
    name.add_argument('--packname',
                      help='Force pack name (disadvised, and ignored for main packs).',
                      default='__guess__')
    name.add_argument('--prefix',
                      help='Force prefix (before release) in pack name. Main packs only. Defaults to user from git_ref. "" for no prefix',
                      default='__user__')
    parser.add_argument('--populate_filter_file',
                        help='Filter file (list of files to be filtered) for populate time (defaults from within ial_build package).',
                        default='__inconfig__')
    parser.add_argument('--link_filter_file',
                        help='Filter file (list of files to be filtered) for link time (defaults from within ial_build package).',
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
        if args.prefix != '__user__':
            print("Incr pack: argument --prefix ignored.")
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
                                ask_confirmation=True,
                                remove_ics_=False,
                                fetch=args.fetch,
                                start_ref=args.start_ref)
    else:
        if args.packname != '__guess__':
            print("Main pack: argument --packname ignored.")
        IA4H_gitref_to_main_pack(args.repository,
                                 args.git_ref,
                                 args.compiler_label,
                                 compiler_flag=args.compiler_flag,
                                 homepack=args.homepack,
                                 populate_filter_file=args.populate_filter_file,
                                 link_filter_file=args.link_filter_file,
                                 silent=False,
                                 ask_confirmation=True,
                                 prefix=args.prefix,
                                 remove_ics_=False,
                                 fetch=args.fetch)
