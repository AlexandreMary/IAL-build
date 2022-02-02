#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Building executables algorithms.
"""
import six
import json
import os
import copy
import shutil

from .repositories import IALview
from .pygmkpack import (Pack, PackError, GmkpackTool,
                        USUAL_BINARIES)

# TODO: handle multiple repositories/projects to pack


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
    :param packtype: type of pack, among ('incr', 'main')
    :param compiler_label: gmkpack compiler label
    :param compiler_flag: gmkpack compiler flag
    :param abspath: True if the absolute path to pack is requested (instead of basename)
    :param homepack: home of pack
    :param to_bin: True if the path to binaries subdirectory is requested
    """
    packname = GmkpackTool.guess_pack_name(git_ref, compiler_label, compiler_flag,
                                           pack_type=packtype)
    # finalisation
    path_elements = [packname]
    if abspath:
        path_elements.insert(0, GmkpackTool.get_homepack())
    if to_bin:
        path_elements.append('bin')
    return os.path.join(*path_elements)


def IAL_gitref_to_incrpack(repository,
                           git_ref,
                           compiler_label,
                           compiler_flag=None,
                           start_ref=None,
                           packname='__guess__',
                           preexisting_pack=False,
                           clean_if_preexisting=True,
                           homepack=None,
                           rootpack=None,
                           silent=False,
                           ask_confirmation=False,
                           remove_ics_=True,
                           fetch=False):
    """
    From git ref to incremental pack.

    :param repository: Git repository to be used
    :param git_ref: Git reference (branch, tag) to be exported
    :param compiler_label: Gmkpack's compiler label to be used
    :param compiler_flag: Gmkpack's compiler flag to be used
    :param start_ref: increment of modification starts from this ref.
        If None, starts from latest official tagged ancestor.
    :param packname: name of the pack;
        if '__guess__' (recommended), auto generated;
        if None, defaults to **git_ref**
    :param preexisting_pack: assume the pack already exists
    :param clean_if_preexisting: call cleanpack before populating
    :param homepack: directory in which to build pack
    :param rootpack: where to look for root packs
    :param silent: to hide gmkpack's stdout
    :param ask_confirmation: ask for confirmation about the pack
        before actually creating pack and populating
    :param remove_ics_: to remove the ics_ file.
    :param fetch: to fetch branch on remote or not
    """
    if packname is None:
        packname = git_ref
    elif packname == '__guess__':
        packname = guess_packname(git_ref,
                                  compiler_label,
                                  'incr',
                                  compiler_flag=compiler_flag)
    print("-" * 50)
    print("Start export of git ref: '{}' to incremental pack: '{}'".format(git_ref, packname))
    if ask_confirmation:
        ok = six.moves.input("Confirm ? [y/n] ")
        if ok == 'n':
            print("Confirmation cancelled: exit.")
            exit()
        elif ok != 'y':
            print("Please answer by 'y' or 'n'. Exit.")
            exit()
    os.environ['GMK_RELEASE_CASE_SENSITIVE'] = '1'
    view = IALview(repository, git_ref, fetch=fetch)
    try:
        if preexisting_pack:
            pack = Pack(packname, preexisting=preexisting_pack, homepack=homepack)
            if clean_if_preexisting:
                pack.cleanpack()
        else:
            if start_ref is None:
                ancestor_info = view.latest_official_branch_from_main_release
            else:
                ref_split = view.split_ref(start_ref)
                ancestor_info = {'radical':ref_split['radical'],
                                 'version':ref_split['version']}
            pack = GmkpackTool.new_incremental_pack(packname,
                                                    compiler_label,
                                                    view.latest_main_release_ancestor,
                                                    initial_branch=ancestor_info.get('radical', None),
                                                    initial_branch_version=ancestor_info.get('version', None),
                                                    compiler_flag=compiler_flag,
                                                    homepack=homepack,
                                                    rootpack=rootpack,
                                                    silent=silent)
            if remove_ics_:
                pack.ics_remove('')  # for it to be re-generated at compile time, with proper options
        pack.populate_from_IALview_as_incremental(view, start_ref=start_ref)
    except Exception:
        print("Failed export of git ref to pack !")
        del view  # to restore the repository state
        raise
    else:
        print("Sucessful export of git ref: {} to pack: {}".format(git_ref, pack.abspath))
    finally:
        print("-" * 50)
    return pack


def IAL_gitref_to_main_pack(repository,
                            git_ref,
                            compiler_label,
                            compiler_flag=None,
                            homepack=None,
                            populate_filter_file='__inconfig__',
                            link_filter_file='__inconfig__',
                            silent=False,
                            ask_confirmation=False,
                            prefix='__user__',
                            remove_ics_=True,
                            fetch=False):
    """
    From git ref to main pack.

    :param repository: Git repository to be used
    :param git_ref: Git reference (branch, tag) to be exported
    :param compiler_label: Gmkpack's compiler label to be used
    :param compiler_flag: Gmkpack's compiler flag to be used
    :param homepack: directory in which to build pack
    :param populate_filter_file: filter file (list of files to be filtered)
        for populate time (defaults from within ial_build package)
    :param link_filter_file: filter file (list of files to be filtered)
        for link time (defaults from within ial_build package)
    :param silent: to hide gmkpack's stdout
    :param ask_confirmation: ask for confirmation about the pack
        before actually creating pack and populating
    :param prefix: '__user__' or None.
    :param remove_ics_: to remove the ics_ file.
    :param fetch: to fetch branch on remote or not
    """
    print("-" * 50)
    print("Start export of git ref: '{}' to main pack".format(git_ref))
    if ask_confirmation:
        ok = six.moves.input("Confirm ? [y/n] ")
        if ok == 'n':
            print("Confirmation cancelled: exit.")
            exit()
        elif ok != 'y':
            print("Please answer by 'y' or 'n'. Exit.")
            exit()
    os.environ['GMK_RELEASE_CASE_SENSITIVE'] = '1'
    # prepare args
    args = GmkpackTool.args4mainpack_from_IAL_git_ref(git_ref, repository)
    args.update(GmkpackTool.args4pack_general(compiler_label=compiler_label,
                                              compiler_flag=compiler_flag,
                                              homepack=homepack))
    try:
        # make pack
        pack = GmkpackTool.create_mainpack_from_args(args, silent=silent)
        if remove_ics_:
            pack.ics_remove('')  # for it to be re-generated at compile time, with proper options
        pack.populate_hub(view.latest_main_release_ancestor)  # to build hub packages
        pack.populate_from_IALview_as_main(view,
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


def IALgitref2pack(IAL_git_ref,
                   IAL_repo_path,
                   pack_type='incr',
                   preexisting_pack=False,
                   clean_if_preexisting=False,
                   compiler_label=None,
                   compiler_flag=None,
                   homepack=None,
                   rootpack=None):
    """
    Make a pack out of a bundle.

    :param pack_type: type of pack, among ('incr', 'main')
    :param preexisting_pack: assume the pack already preexists
    :param clean_if_preexisting: if True, call cleanpack before populating a preexisting pack
    :param compiler_label: Gmkpack's compiler label to be used
    :param compiler_flag: Gmkpack's compiler flag to be used
    :param homepack: directory in which to build pack
    :param rootpack: diretory in which to look for root pack (incr packs only)
    """
    view = IALview(IAL_repo_path, IAL_git_ref)
    # pack
    if not preexisting_pack:
        args = GmkpackTool.getargs(pack_type,
                                   IAL_git_ref,
                                   IAL_repo_path,
                                   compiler_label=compiler_label,
                                   compiler_flag=compiler_flag,
                                   homepack=homepack,
                                   rootpack=rootpack)
        try:
            pack = GmkpackTool.create_pack_from_args(args, pack_type)
        except Exception:
            print("Creation of pack failed !")
            raise
    else:
        packname = GmkpackTool.guess_pack_name(IAL_git_ref, compiler_label, compiler_flag,
                                               pack_type=pack_type,
                                               IAL_repo_path=IAL_repo_path)
        pack = Pack(packname,
                    homepack=GmkpackTool.get_homepack(homepack))
        if clean_if_preexisting:
            pack.cleanpack()
    # then populate
    if pack_type == 'main':
        pack.populate_from_IALview_as_main(view)
    elif pack_type == 'incr':
        pack.populate_from_IALview_as_incremental(view)
    print("Pack successfully populated: " + pack.abspath)
    return pack


def parse_programs(programs):
    if isinstance(programs, six.string_types):
        if programs == '__usual__':
            programs = USUAL_BINARIES
        else:
            programs = [p.strip() for p in programs.split(',')]
    elif not isinstance(programs, list):
        raise TypeError("**programs** must be a string (e.g. 'MASTERODB,BATOR') or a list")
    return programs


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
    # preprocess args
    if isinstance(pack, six.string_types):
        pack = Pack(pack, preexisting=True, homepack=homepack)
    elif not isinstance(pack, Pack):
        raise PackError("**pack** argument must be a pack name or a Pack instance")
    programs = parse_programs(programs)
    build_report = {}
    # start by compiling sources without any executable
    print("-" * 50)
    print("Start compilation...")
    try:
        if not pack.ics_available_for('') or regenerate_ics:
            print("(Re-)generate ics_ script ...")
            pack.ics_build_for('', **other_options)
    except Exception as e:
        message = "... ics_ generation failed: {}".format(str(e))
        print(message)
        build_report['compilation'] = {'OK':False, 'Output':message}
    else:
        print("Run ics_ ...")
        compile_output = pack.compile('',
                                      silent=silent,
                                      clean_before=cleanpack,
                                      fatal=False)
        if compile_output['OK']:
            print("... compilation OK !")
        else:  # build failed but not fatal
            print("... compilation failed !")
            if not silent:
                print("-> compilation output: {}".format(compile_output['Output']))
        print("-" * 50)
        build_report['compilation'] = compile_output
    # Executables
    if not pack.is_incremental:
        # pack main: assume compilation and libs ok from ics_ and skip updates 
        other_options = copy.copy(other_options)
        other_options['no_compilation'] = True
        other_options['no_libs_update'] = True
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
            print("Run ics_{} ...".format(program))
            compile_output = pack.compile(program,
                                          silent=silent,
                                          clean_before=False,
                                          fatal=fatal_build_failure=='__any__')
            if compile_output['OK']:
                print("... {} OK !".format(program))
            else:  # build failed but not fatal
                print("... {} failed !".format(program))
                if not silent:
                    print("-> build output: {}".format(compile_output['Output']))
            print("-" * 50)
            build_report[program] = compile_output
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

