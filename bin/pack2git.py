#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Create or populate a Git branch from a pack.
"""
import os
import argparse

from ia4h_scm.pygmkpack import Pack
from ia4h_scm.repositories import IA4Hview
from ia4h_scm.algos import IA4H_gitref_to_incrpack, IA4H_gitref_to_main_pack


DEFAULT_GIT_REPO = os.path.join(os.environ['HOME'], 'git-dev', 'arpifs')


def pack2git(packname, repository,
             branchname=None,
             files_to_delete=[],
             homepack=None,
             preexisting_branch=False,
             commit_message=None,
             register_in_GCOdb=True):
    """
    Create or populate a Git branch from a pack.
    
    For arguments, cf. ia4h_scm.pygmkpack.Pack()
    and ia4h_scm.pygmkpack.Pack.save_as_IA4H_branch()
    """
    pack = Pack(packname, homepack=homepack)
    branch = pack.save_as_IA4H_branch(repository,
                                      files_to_delete=files_to_delete,
                                      branchname=branchname,
                                      commit_message=commit_message,
                                      preexisting_branch=preexisting_branch,
                                      ask_confirmation=True,
                                      register_in_GCOdb=register_in_GCOdb)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create or populate a Git branch from a pack.')
    parser.add_argument('pack',
                        help='Pack: packname (in HOMEPACK or to specify with --homepack).')
    parser.add_argument('-b', '--branch_name',
                        help='Customized name of the branch to be populated from pack. By default, try to guess from pack.',
                        default=None)
    parser.add_argument('-r', '--repository',
                        help='Location of the Git repository in which to populate branch (defaults to: {}).'.format(DEFAULT_GIT_REPO),
                        default=DEFAULT_GIT_REPO)
    parser.add_argument('-d', '--files_to_delete',
                        help='Indicate a file containing the local name of files to be deleted in the repository.',
                        default=[])
    parser.add_argument('-e', '--preexisting_branch',
                        action='store_true',
                        help='To assume the branch already exists.',
                        default=False)
    parser.add_argument('-c', '--commit_message',
                        help='To commit the modifications with the provided commit message.',
                        default=None)
    parser.add_argument('--homepack',
                        default=None,
                        help='To specify a home directory for packs (defaults to $HOMEPACK or $HOME/pack)')
    parser.add_argument('-g', '--gco',
                        action='store_true',
                        help='Register branch in GCO database (required to later push/git_post to GCO). REQUIRES git_branch tool from GCO.',
                        default=False)
    args = parser.parse_args()

    pack2git(args.pack,
             repository=args.repository,
             branchname=args.branch_name,
             files_to_delete=args.files_to_delete,
             homepack=args.homepack,
             preexisting_branch=args.preexisting_branch,
             commit_message=args.commit_message,
             register_in_GCOdb=args.gco)
