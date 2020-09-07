#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Create or populate a Git branch from a pack.
"""
import argparse

from ia4h_scm.pygmkpack import Pack
from ia4h_scm.repositories import IA4H_Branch
from ia4h_scm.algos import IA4H_gitref_to_incrpack, IA4H_gitref_to_main_pack


def pack2branch(packname, repository,
                branchname=args.branch_name,
                homepack=None,
                preexisting_branch=False,
                commit_message=None,
                dry_run=False):
    """
    """
    pack = Pack(packname, homepack=homepack)
    branch = pack.save_as_IA4H_Branch(repository,
                                      branchname=branchname,
                                      commit_message=commit_message,
                                      preexisting_branch=preexisting_branch,
                                      push=False,
                                      ask_confirmation=True,
                                      dry_run=dry_run)
    print("!Warning! if files are to be deleted, please do so manually in the branch ('git rm <file>')")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create or populate a Git branch from a pack.')
    parser.add_argument('pack',
                        help='Pack: packname (in HOMEPACK or to specify with --homepack).')
    parser.add_argument('-b', '--branch_name',
                        help='Customized name of the branch to be populated from pack.',
                        default='__guess_from_pack__')
    parser.add_argument('-r', '--repository',
                        help='Location of the Git repository in which to populate branch.',
                        default=os.path.join(os.env['HOME'], 'git-dev', 'arpifs'))
    parser.add_argument('-e', '--preexisting_branch',
                        type=bool,
                        action='store_true',
                        help='To assume the branch already exists.',
                        default=False)
    parser.add_argument('-c', '--commit_message',
                        help='To commit the modifications with the provided commit message.',
                        default=None)
    parser.add_argument('--homepack',
                        default=None,
                        help='To specify a home directory for packs (defaults to $HOMEPACK or $HOME/pack)')
    parser.add_argument('-d', '--dry',
                        type=bool,
                        action='store_true',
                        help='Dry run. Do no actually populate branch.',
                        default=False)
    args = parser.parse_args()

    pack2branch(args.pack,
                repository=args.repository,
                branchname=args.branch_name,
                homepack=args.homepack,
                preexisting_branch=args.preexisting_branch,
                commit_message=args.commit_message,
                dry_run=args.dry)
