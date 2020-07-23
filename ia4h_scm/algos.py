#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Building executables algorithms.
"""
import six
import json

from .repositories import IA4H_Branch
from .pygmkpack import (Pack, PackError,
                        new_incremental_pack,
                        GCO_ROOTPACK, USUAL_BINARIES)

# TODO: handle multiple repositories/projects to pack

def branch2pack(repository, branch,
                packname=None,
                preexisting_pack=False,
                clean_if_preexisting=True,
                homepack=None,
                rootpacks_dir=GCO_ROOTPACK,
                other_pack_options={},
                silent=False):
    """From branch(es) to pack."""
    if packname is None:
        packname = branch.name
    print("-" * 50)
    print("Start export of branch '{}' to pack '{}'".format(branch, packname))
    branch = IA4H_Branch(repository, branch)
    try:
        if preexisting_pack:
            pack = Pack(packname, preexisting=preexisting_pack, homepack=homepack)
            if clean_if_preexisting:
                pack.cleanpack()
        else:
            ancestor_info = branch.latest_official_branch_from_main_release
            pack = new_incremental_pack(packname,
                                        branch.latest_main_release_ancestor,
                                        initial_branch=ancestor_info.get('b', None),
                                        initial_branch_version=ancestor_info.get('v', None),
                                        homepack=homepack,
                                        from_root=rootpacks_dir,
                                        other_pack_options=other_pack_options,
                                        silent=silent)
        pack.populate_from_IA4H_branch(branch)
    except Exception:
        print("Failed export of branch to pack !")
        del branch  # to restore the repository state
        raise
    else:
        print("Sucessful export of branch to pack: {}".format(pack.abspath))
    finally:
        print("-" * 50)
    return pack


def pack_build_executables(pack,
                           programs=USUAL_BINARIES,
                           silent=False,
                           regenerate_ics=True,
                           cleanpack=True,
                           other_options={},
                           homepack=None,
                           fatal_build_failure='__any__',
                           dump_build_report=False):
    """Build pack executables."""
    if isinstance(pack, six.string_types):
        pack = Pack(pack, preexisting=True, homepack=homepack)
    elif not isinstance(pack, Pack):
        raise PackError("**pack** argument must be a pack name or a Pack instance")
    if isinstance(programs, six.string_types):
        programs = [p.strip() for p in programs.split(',')]
    elif not isinstance(programs, list):
        raise TypeError("**programs** must be a string (e.g. 'MASTERODB,BATOR') or a list")
    build_report = {}
    first = True
    for program in programs:
        print("-" * 50)
        print("Build: {} ...".format(program))
        try:
            print("need to generate ics_",
                  not pack.ics_available_for(program),
                  regenerate_ics,
                  not pack.ics_available_for(program) or regenerate_ics)
            if not pack.ics_available_for(program) or regenerate_ics:
                print("(Re-)generate ics_{} script ...".format(program.lower()))
                pack.ics_build_for(program, **other_options)
        except Exception as e:
            message = "... ics_{} generation failed: {}".format(program, str(e))
            print(message)
            if fatal_build_failure == '__any__':
                raise
            else:
                build_report[program] = {'OK':False, 'Output':message}
        else:  # ics_ generation OK
            print("Run ics_ ...")
            compile_output = pack.compile(program,
                                          silent=silent,
                                          clean_before=cleanpack and first,
                                          fatal=fatal_build_failure=='__any__')
            if compile_output['OK']:
                print("... {} OK !".format(program))
            else:  # build failed but not fatal
                print("... {} failed !".format(program))
                if not silent:
                    print("-> build output: {}".format(compile_output['Output']))
            print("-" * 50)
            build_report[program] = compile_output
        first = False
    if fatal_build_failure == '__finally__':
        which = [k for k, v in build_report.items() if not v['OK']]
        if len(which) > 0:
            print("Failed builds output(s):")
            for k in which:
                print("{:20}: {}".format(k, build_report[k]['Output']))
            print("-" * 50)
            raise PackError("Build of executable(s) has failed: {}".format(which))
    if dump_build_report:
        with open('build_report.json', 'w') as out:
            json.dump(build_report, out)
    return pack, build_report

