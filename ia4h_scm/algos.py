#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Building executables algorithms.
"""
import six

from .repositories import IA4H_Branch
from .pygmkpack import (Pack, PackError,
                        new_incremental_pack,
                        GCO_ROOTPACK, USUAL_BINARIES)


# TODO: handle multiple repositories/projects to pack


def branch2binaries(repository, branch,
                    programs=USUAL_BINARIES,
                    preexisting_pack=False,
                    rootpacks_dir=GCO_ROOTPACK,
                    other_pack_options={},
                    silent=False):
    """From branch(es) to pack."""
    pack = branch2pack(repository, branch,
                       preexisting_pack=preexisting_pack,
                       rootpacks_dir=rootpacks_dir,
                       other_pack_options=other_pack_options,
                       silent=silent)
    pack_build_executables(pack, programs,
                           silent=silent,
                           other_pack_options=other_pack_options)


def branch2pack(repository, branch,
                preexisting_pack=False,
                rootpacks_dir=GCO_ROOTPACK,
                other_pack_options=None,
                silent=False):
    """From branch(es) to pack."""
    branch = IA4H_Branch(repository, branch)
    if preexisting_pack:
        pack = Pack(branch.name, preexisting=preexisting_pack)
        pack.cleanpack()
    else:
        ancestor_info = branch.latest_official_branch_from_main_release
        pack = new_incremental_pack(branch.name,
                                    branch.latest_main_release_ancestor,
                                    initial_branch=ancestor_info.get('b', None),
                                    initial_branch_version=ancestor_info.get('v', None),
                                    from_root=rootpacks_dir,
                                    other_pack_options=other_pack_options,
                                    silent=silent)
    pack.populate_from_IA4H_branch(branch)
    return pack


def pack_build_executables(pack,
                           programs=USUAL_BINARIES,
                           silent=False,
                           other_pack_options={}):
    """Build pack executables."""
    if isinstance(pack, six.string_types):
        packpack = Pack(packname, preexisting=True)
    elif not isinstance(pack, Pack):
        raise PackError("**pack** argument must be a pack name or a Pack instance")
    for program in programs:
        pack.ics_build_for(program, silent=silent, **other_pack_options)
        pack.compile(program)
    return pack
