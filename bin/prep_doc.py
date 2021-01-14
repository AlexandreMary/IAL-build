#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Prepare doc file for branch.
"""
import os
import argparse
import sys

# Automatically set the python path
package_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, package_path)

from ia4h_scm.repositories import IA4Hview


def main(contrib_ref, start_ref, outdir,
         repository='.'):
    v = IA4Hview(repository, contrib_ref)
    v.prep_doc(outdir, start_ref=start_ref)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare documentation (.tex) for a given branch.')
    parser.add_argument('branch',
                        help='Git ref of the branch.')
    parser.add_argument('-s', '--start_ref',
                        help='Starting ref of the branch, if incremental to another branch/ref.',
                        default=None)
    parser.add_argument('-r', '--repository',
                        help="Location of the Git repository (defaults to: '.').",
                        default='.')
    parser.add_argument('--outdir',
                        help="Output directory in which to save doc file.",
                        default=os.environ.get('IA4H_DOC_OUTDIR'))
    args = parser.parse_args()
    if args.outdir in (None, ''):
        raise ValueError("Output directory must be provided through arg --outdir or env var IA4H_DOC_OUTDIR.")
    main(args.branch, args.start_ref,
         outdir=args.outdir,
         repository=args.repository)
