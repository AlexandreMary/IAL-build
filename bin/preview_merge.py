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
package_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, package_path)

from ia4h_scm.repositories import GitProxy

conflicts_types_legend = {
    'M':'MODIFIED',
    'A':'ADDED',
    'T':'TYPE-CHANGED',
    'D':'DELETED',
    'C':'COPIED',
    'R':'RENAMED'
    }


def main(contrib_ref, target_ref,
         common_ancestor=None,
         repository='.'):
    g = GitProxy(repository)
    potential_conflicts = g.preview_merge(contrib_ref, target_ref, common_ancestor=common_ancestor)
    for conflict_type, files in potential_conflicts.items():
        legend = '{} in contrib / {} in target:'.format(conflicts_types_legend[conflict_type[0]],
                                                        conflicts_types_legend[conflict_type[2]])
        print("")
        print(legend)
        print("-" * len(legend))
        for f in files:
            print("  {}".format(f))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get a preview of merging a contribution on a target (integration) branch.')
    parser.add_argument('contrib_ref',
                        help='Git ref (branch or tag) of the contribution - to be merged.')
    parser.add_argument('target_ref',
                        help='Git ref (branch or tag) of the integration branch - in which to merge.')
    parser.add_argument('-r', '--repository',
                        help="Location of the Git repository (defaults to: '.').",
                        default='.')
    parser.add_argument('--common_ancestor',
                        help="Specify the common ancestor since which to estimate modifications on both sides (auto-determined otherwise).",
                        default=None)
    args = parser.parse_args()
   
    main(args.contrib_ref, args.target_ref,
         common_ancestor=args.common_ancestor,
         repository=args.repository)

