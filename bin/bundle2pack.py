#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Make or populate a pack from a bundle.
"""
import os
import argparse
import sys

# Automatically set the python path
repo_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(repo_path, 'src'))

from ial_build.algos import bundle2pack
from ial_build.pygmkpack import GmkpackTool
from ial_build.config import DEFAULT_BUNDLE_CACHE_DIR


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make or populate a pack from a bundle.')
    parser.add_argument('bundle',
                        help='bundle: path to bundle file.')
    parser.add_argument('-l', '--compiler_label',
                        help='Compiler label. Through $GMKFILE, defaults to: "{}".'.format(
                            GmkpackTool.get_compiler_label()),
                        default=GmkpackTool.get_compiler_label())
    parser.add_argument('-o', '--compiler_flag',
                        help='Compiler flag. Defaults to $GMK_OPT: "{}".'.format(
                            GmkpackTool.get_compiler_flag()),
                        default=GmkpackTool.get_compiler_flag())
    parser.add_argument('-t', '--pack_type',
                        help='Type of pack (default: incr).',
                        default='incr',
                        choices=['incr', 'main'])
    parser.add_argument('-u', '--no_update',
                        action='store_false',
                        help='Do not try to update local repos, so that non-commited modifications in repos are' +
                        'included. BEWARE that the checkedout version in each repo may then not be consistent' +
                        'with the version requested in the bundle.',
                        dest='update',
                        default=True)
    parser.add_argument('-e', '--preexisting_pack',
                        action='store_true',
                        help='Assume the pack already preexists (protection against unhappy overwrites).',
                        default=False)
    parser.add_argument('-c', '--clean_if_preexisting',
                        action='store_true',
                        help='Call cleanpack.',
                        default=False)
    parser.add_argument('-p', '--programs',
                        help="Programs which ics_{p} script to be generated, e.g. 'masterodb' or 'masterodb,bator'. " +
                        "If none, only compilation script (ics_) is generated; " +
                        "other scripts can be generated later, using commandline in the pack's .genesis file " +
                        "and adding -p argument.",
                        default='')
    parser.add_argument('-d', '--cache_directory',
                        help='Cache directory: where git repos are downloaded/updated before populating pack. ' +
                             'Defaults to $HOME/bundles: ' + DEFAULT_BUNDLE_CACHE_DIR,
                        default=DEFAULT_BUNDLE_CACHE_DIR)
    parser.add_argument('--homepack',
                        default=GmkpackTool.get_homepack(),
                        help='To specify a home directory for packs. Defaults to $HOMEPACK or $HOME/pack: ' +
                        GmkpackTool.get_homepack())
    parser.add_argument('-f', '--rootpack',
                        help="Home of root packs to start from, for incremental packs. " +
                        "Defaults to Gmkpack's $ROOTPACK: {}".format(GmkpackTool.get_rootpack()),
                        default=GmkpackTool.get_rootpack())
    args = parser.parse_args()

    pack = bundle2pack(args.bundle,
                       pack_type=args.pack_type,
                       update=args.update,
                       preexisting_pack=args.preexisting_pack,
                       clean_if_preexisting=args.clean_if_preexisting,
                       compiler_label=args.compiler_label,
                       compiler_flag=args.compiler_flag,
                       homepack=args.homepack,
                       rootpack=args.rootpack)
    if args.programs != '':
        for p in GmkpackTool.parse_programs(args.programs):
            pack.ics_build_for(p, GMK_THREADS=4)
