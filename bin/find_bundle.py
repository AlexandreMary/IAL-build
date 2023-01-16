#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Find the most recent bundle tag(s) in IAL-bundle repository, available for an IAL git reference.
"""
import os
import argparse
import sys

# Automatically set the python path
repo_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(repo_path, 'src'))

from ial_build.bundle import TmpIALbundleRepo
from ial_build.config import (DEFAULT_IAL_REPO,
                              DEFAULT_IALBUNDLE_REPO)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find the most recent bundle tag(s) in IAL-bundle repository, ' +
                                                 'available for an IAL git reference.')
    parser.add_argument('git_ref',
                        help='Git ref: branch or tag. WARNING: if none is provided, the currently checked out ref is taken.',
                        nargs='?',
                        default=None)
    parser.add_argument('--get_copy',
                        help="Get a local copy of the bundle file, if only one.",
                        action='store_true')
    parser.add_argument('-r', '--repository',
                        help='Location of the IAL Git repository (defaults to: {}).'.format(DEFAULT_IAL_REPO),
                        default=DEFAULT_IAL_REPO)
    parser.add_argument('-v', '--verbose',
                        action='store_true')
    parser.add_argument('-f', '--force_overwrite',
                        help="To allow overwriting of existing target file (if --get_copy)",
                        dest='overwrite',
                        action='store_true')
    parser.add_argument('--IAL_bundle_origin_repo',
                        help="URL of the 'IAL-bundle' repository to clone. " +
                             "Default: " + DEFAULT_IALBUNDLE_REPO,
                        default=DEFAULT_IALBUNDLE_REPO)
    args = parser.parse_args()
    IALbundles = TmpIALbundleRepo(args.IAL_bundle_origin_repo, verbose=args.verbose)
    IALbundles.print_bundle_tags_for_IAL_git_ref(args.repository,
                                                 args.git_ref,
                                                 verbose=args.verbose)
    if args.get_copy:
        IALbundles.get_bundle_for_IAL_git_ref(args.repository,
                                              args.git_ref,
                                              to_file='__tag__',
                                              overwrite=args.overwrite)
