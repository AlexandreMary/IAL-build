#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Make and checkout a new IAL branch with the GCO-classical nomenclature (<user>_<release>_<radical>),
based on a given reference.
"""
import os
import argparse
import sys

# Automatically set the python path
repo_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(repo_path, 'src'))

from ial_build.repositories import IALview, GitProxy


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
'Make and checkout a new IAL branch with the GCO-classical nomenclature (<user>_<release>_<radical>), ' +
'based on a given reference.')
    parser.add_argument('branch_radical',
                        help='Branch radical: the branch will be named <logname>_<release>_<branch_radical>.')
    parser.add_argument('-s', '--start_reference',
                        help='Reference of the start of the branch. ' +
                             'Can be a tag, commit, branch (! careful in this latter case). ' +
                             'Default is HEAD.',
                        default='HEAD')
    args = parser.parse_args()
    v = IALview('.', args.start_reference)
    b = v.new_branch_classical_nomenclature(args.branch_radical)
    del v
    r = GitProxy('.')
    r.checkout_new_branch(b, start_ref=args.start_reference)
