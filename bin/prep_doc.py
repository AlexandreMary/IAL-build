#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Prepare doc file for branch.
"""
import os
import argparse
import sys

# Automatically set the python path
repo_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(repo_path, 'src'))

from ial_build.repositories import IALview
from ial_build.config import IAL_DOC_OUTPUT_DIR


def main(contrib_ref,
         start_ref,
         from_oldest_common_ancestor_with_branch,
         metadata,
         outdir,
         repository='.'):
    v = IALview(repository, contrib_ref)
    v.prep_doc(metadata,
               outdir=outdir,
               from_start_ref=start_ref,
               from_oldest_common_ancestor_with=from_oldest_common_ancestor_with_branch)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare documentation (.tex) for a given branch.')
    ref = parser.add_mutually_exclusive_group(required=True)
    ref.add_argument('-s', '--start_ref',
                     help='Starting ref of the branch, if incremental to another branch/ref. ' +
                          'This should be selected for the firstly integrated branch.',
                     default=None)
    ref.add_argument('-b', '--from_oldest_common_ancestor_with_branch',
                     help='Consider the branch from the oldest common ancestor with the given branch. ' +
                          'Typically, integration branch.',
                     default=None)
    #metadata = parser.add_mutually_exclusive_group(required=True)
    #metadata_f = metadata.add_subparsers('metadata_file')
    #metadata = parser.add_subparsers('metadata', 'Subparser for metadata', required=True)
    metadata = parser.add_subparsers(required=True)
    metadata_f = metadata.add_parser('metadata_file',
                                     help='To pass metadata through a file.')
    metadata_f.add_argument('metadata_file',
                            help='A metadata file, formatted as json, containing expected metadata.')
    metadata_a = metadata.add_parser('metadata_args',
                                     help='To pass metadata as args.')
    repro = metadata_a.add_mutually_exclusive_group(required=True)
    repro.add_argument('-r', '--bit_repro',
                       action='store_true',
                       help="Bit-reproducible contribution.")
    repro.add_argument('-n', '--numerical_impact',
                       help="Expected numerical impact, if any (otherwise use arg -r): " +
                            "in terms of scope of configs, variables and magnitude of numerical impact.")
    metadata_a.add_argument('-d', '--oneline_doc',
                            help="A short, 'one-line', documentation of the branch",
                            required=True)
    metadata_a.add_argument('-a', '--authors',
                            help="Authors of the contribution")
    parser.add_argument('-r', '--repository',
                        help="Location of the Git repository (defaults to: '.').",
                        default='.')
    parser.add_argument('--outdir',
                        help="Output directory in which to save doc file. Default to '{}'.".format(IAL_DOC_OUTPUT_DIR),
                        default=IAL_DOC_OUTPUT_DIR)
    parser.add_argument('branch',
                        help='Git ref of the branch.')
    args = parser.parse_args()
    if 'metadata_file' in args:
        metadata = json.load(args.metadata_file)
    else:
        metadata = dict(oneline_doc=args.oneline_doc,
                        numerical_impact=None if args.bit_repro else args.numerical_impact)
        if args.authors is not None:
            metadata['authors'] = args.authors
    main(args.branch,
         start_ref=args.start_ref,
         from_oldest_common_ancestor_with_branch=args.from_oldest_common_ancestor_with_branch,
         metadata=metadata,
         outdir=args.outdir,
         repository=args.repository)
