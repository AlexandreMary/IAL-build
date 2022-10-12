#!/usr/bin/env python3
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

from ial_build.algos import IALgitref2pack
from ial_build.pygmkpack import GmkpackTool
from ial_build.config import (DEFAULT_IAL_REPO,
                              DEFAULT_IALBUNDLE_REPO,
                              DEFAULT_BUNDLE_CACHE_DIR,
                              DEFAULT_PACK_COMPILER_FLAG)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make or populate a pack from Git.')
    parser.add_argument('git_ref',
                        help='Git ref: branch or tag.')
    parser.add_argument('-l', '--compiler_label',
                        default=GmkpackTool.get_compiler_label(fatal=False),
                        help='Compiler label (default: {}).'.format(GmkpackTool.get_compiler_label(fatal=False)))
    parser.add_argument('-o', '--compiler_flag',
                        help='Compiler flag (default: {}).'.format(DEFAULT_PACK_COMPILER_FLAG),
                        default=DEFAULT_PACK_COMPILER_FLAG)
    parser.add_argument('-t', '--packtype',
                        help='Type of pack (default: incr).',
                        default='incr',
                        choices=['incr', 'main'])
    parser.add_argument('-n', '--threads_number',
                        help='Number of threads to be set in compilation script.',
                        default=10)
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
    parser.add_argument('--hub_bundle_repo_path', '--hbrp',
                        help="Main packs only: path to the 'IAL-bundle' repository, " +
                             "that contains bundle for populating hub packages in a main pack. " +
                             "Default: " + DEFAULT_IALBUNDLE_REPO,
                        default=DEFAULT_IALBUNDLE_REPO)
    parser.add_argument('--hub_bundle_cache_dir', '--hbcd',
                        help="Main packs only: path to the directory in which to find/download bundled hub packages. " +
                             "Default: " + DEFAULT_BUNDLE_CACHE_DIR,
                        default=DEFAULT_BUNDLE_CACHE_DIR)
    parser.add_argument('--hub_bundle_update_not', '--hbun',
                        action='store_false',
                        dest='hub_bundle_update',
                        help="Main packs only: not to update=download bundled hub packages from their remote, " +
                             "so that no 'git fetch' and 'git checkout' is required",
                        default=True)
    args = parser.parse_args()
    pack = IALgitref2pack(args.git_ref,
                          args.repository,
                          bundle_repo_path=args.hub_bundle_repo_path,
                          bundle_cache_dir=args.hub_bundle_cache_dir,
                          bundle_update=args.hub_bundle_update,
                          pack_type=args.packtype,
                          preexisting_pack=args.preexisting_pack,
                          clean_if_preexisting=args.clean_if_preexisting,
                          compiler_label=args.compiler_label,
                          compiler_flag=args.compiler_flag,
                          homepack=args.homepack,
                          rootpack=args.rootpack)
    pack.ics_tune('', GMK_THREADS=int(args.threads_number))
    if args.programs != '':
        for p in GmkpackTool.parse_programs(args.programs):
            pack.ics_build_for(p)
            pack.ics_tune(p, GMK_THREADS=int(args.threads_number))
