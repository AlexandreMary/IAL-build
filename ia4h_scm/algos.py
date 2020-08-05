#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Building executables algorithms.
"""
import six
import json
import os

from .repositories import IA4Hview
from .pygmkpack import (Pack, PackError, GmkpackTool,
                        USUAL_BINARIES)

# TODO: handle multiple repositories/projects to pack

def prefix_from_user(user=None):
    return 'CY' if user is None else (user + '_CY')


def guess_packname(git_ref,
                   compiler_label,
                   packtype,
                   compiler_flag=None,
                   abspath=False,
                   homepack=None,
                   to_bin=False):
    """
    Guess pack name from a number of arguments.
    
    :param git_ref: Git reference to be exported to pack
    :param compiler_label: gmkpack compiler label
    :param packtype: type of pack, among ('incr', 'main')
    :param compiler_flag: gmkpack compiler flag
    :param abspath: True if the absolute path to pack is requested (instead of basename)
    :param homepack: home of pack
    :param to_bin: True if the path to binaries subdirectory is requested
    """
    if homepack is None:
        homepack = GmkpackTool.get_homepack()
    ref_split = IA4Hview.split_ref(git_ref)
    if packtype == 'main':
        args = GmkpackTool.args_for_main_commandline(ref_split['release'],
                                                     ref_split['radical'],
                                                     ref_split['version'],
                                                     compiler_label,
                                                     compiler_flag=compiler_flag,
                                                     prefix=prefix_from_user(ref_split['user']),
                                                     homepack=homepack)
        packname = GmkpackTool.args2packname(args, mainpack=(packtype=='main'))
    elif packtype == 'incr':
        assert compiler_flag is not None
        packname = '.'.join([git_ref, compiler_label, compiler_flag])
    path_elements = [packname]
    if abspath:
        path_elements.insert(0, homepack)
    if to_bin:
        path_elements.append('bin')
    return os.path.join(*path_elements)


def IA4H_gitref_to_incrpack(repository,
                            git_ref,
                            compiler_label,
                            compiler_flag=None,
                            packname=None,
                            preexisting_pack=False,
                            clean_if_preexisting=True,
                            homepack=None,
                            rootpack=None,
                            silent=False):
    """From git ref to incremental pack."""
    if packname is None:
        packname = git_ref
    elif packname == '__guess__':
        packname = guess_packname(git_ref,
                                  compiler_label,
                                  'incr',
                                  compiler_flag=compiler_flag)
    print("-" * 50)
    print("Start export of git ref: '{}' to pack: '{}'".format(git_ref, packname))
    view = IA4Hview(repository, git_ref)
    try:
        if preexisting_pack:
            pack = Pack(packname, preexisting=preexisting_pack, homepack=homepack)
            if clean_if_preexisting:
                pack.cleanpack()
        else:
            ancestor_info = view.latest_official_branch_from_main_release
            pack = GmkpackTool.new_incremental_pack(packname,
                                                    compiler_label,
                                                    view.latest_main_release_ancestor,
                                                    initial_branch=ancestor_info.get('b', None),
                                                    initial_branch_version=ancestor_info.get('v', None),
                                                    compiler_flag=compiler_flag,
                                                    homepack=homepack,
                                                    rootpack=rootpack,
                                                    silent=silent)
        pack.populate_from_IA4Hview_as_incremental(view)
    except Exception:
        print("Failed export of git ref to pack !")
        del view  # to restore the repository state
        raise
    else:
        print("Sucessful export of git ref: {} to pack: {}".format(git_ref, pack.abspath))
    finally:
        print("-" * 50)
    return pack


def IA4H_gitref_to_main_pack(repository,
                             git_ref,
                             compiler_label,
                             compiler_flag=None,
                             homepack=None,
                             populate_filter_file='__inconfig__',
                             link_filter_file='__inconfig__',
                             silent=False):
    """From git ref to main pack."""
    print("-" * 50)
    print("Start export of git ref: '{}' to main pack".format(git_ref))
    os.environ['GMK_RELEASE_CASE_SENSITIVE'] = '1'
    view = IA4Hview(repository, git_ref)
    # prepare arguments
    ref_split = view.split_ref(git_ref)
    try:
        # make pack
        pack = GmkpackTool.new_main_pack(ref_split['release'],
                                         ref_split['radical'],
                                         ref_split['version'],
                                         compiler_label,
                                         compiler_flag=compiler_flag,
                                         prefix=prefix_from_user(ref_split['user']),
                                         homepack=homepack,
                                         silent=silent)
        pack.populate_from_IA4Hview_as_main(view,
                                            populate_filter_file=populate_filter_file,
                                            link_filter_file=link_filter_file)
    except Exception:
        print("Failed export of git ref to pack !")
        del view  # to restore the repository state
        raise
    else:
        print("Sucessful export of git ref: {} to pack: {}".format(git_ref, pack.abspath))
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
    os.environ['GMK_RELEASE_CASE_SENSITIVE'] = '1'
    if isinstance(pack, six.string_types):
        pack = Pack(pack, preexisting=True, homepack=homepack)
    elif not isinstance(pack, Pack):
        raise PackError("**pack** argument must be a pack name or a Pack instance")
    if isinstance(programs, six.string_types):
        if programs == '__usual__':
            programs = USUAL_BINARIES
        else:
            programs = [p.strip() for p in programs.split(',')]
    elif not isinstance(programs, list):
        raise TypeError("**programs** must be a string (e.g. 'MASTERODB,BATOR') or a list")
    build_report = {}
    first = True
    for program in programs:
        print("-" * 50)
        print("Build: {} ...".format(program))
        try:
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
        OK = [k for k, v in build_report.items() if v['OK']]
        if len(which) > 0:
            print("Failed builds output(s):")
            for k in which:
                print("{:20}: {}".format(k, build_report[k]['Output']))
            print("-" * 50)
            message = "Build of executable(s) has failed: {}".format(which)
            if len(OK) > 0:
                message += "(OK for: {})".format(OK)
            raise PackError(message)
    if dump_build_report:
        with open('build_report.json', 'w') as out:
            json.dump(build_report, out)
    return pack, build_report

