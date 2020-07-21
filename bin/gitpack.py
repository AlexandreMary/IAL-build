#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Tools for playing with packs (gmkpack) and Git.
"""
import argparse

from ia4h_scm.pygmkpack import Pack
from ia4h_scm.repositories import IA4H_Branch


def pack2branch(packname, repository):
    pack = Pack(packname)
    branch = pack.save_as_IA4H_Branch(repository,
                                      branchname=branchname,
                                      commit_message=commit_message,
                                      preexisting_branch=preexisting_branch,
                                      push=push,
                                      remote=remote)
    print("!Warning! if files are to be deleted, please do so manually in the branch ('git rm <file>')")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Tools for playing with packs (gmkpack) and Git')
    parser.add_argument('action',
                        choices=['pack2branch','branch2pack', 'pack_origin'])
    parser.add_argument('object',
                        help='branch or pack name')
    parser.add_argument('-b', '--branch_name',
                        help='Customized name of the branch to be populated from pack.')
    parser.add_argument('-r', '--repository',
                        default=''
                        help='')
    parser.add_argument('-h', '--homepack',
                        default=None,
                        help='To specify a home directory for packs (defaults to $HOMEPACK or $HOME/pack)')
    parser.add_argument('-f', '--rootpack',
                        help='')
    args = parser.parse_args()

    print(args.action)
    #if args.action == 'pack2branch':
    #    pack2branch()

