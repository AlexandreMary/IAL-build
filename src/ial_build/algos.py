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
from .bundle import IALBundle
from .config import DEFAULT_BUNDLE_CACHE_DIR


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


def bundle2pack(bundle_file,
                pack_type='incr',
                update=True,
                preexisting_pack=False,
                clean_if_preexisting=False,
                cache_dir=DEFAULT_BUNDLE_CACHE_DIR,
                compiler_label=None,
                compiler_flag=None,
                homepack=None,
                rootpack=None):
    """
    Make a pack out of a bundle.

    :param pack_type: type of pack, among ('incr', 'main')
    :param preexisting_pack: assume the pack already preexists
    :param clean_if_preexisting: if True, call cleanpack before populating a preexisting pack
    :param cache_dir: cache directory in which to download/update repositories
    :param compiler_label: Gmkpack's compiler label to be used
    :param compiler_flag: Gmkpack's compiler flag to be used
    :param homepack: directory in which to build pack
    :param rootpack: diretory in which to look for root pack (incr packs only)
    """
    b = IALBundle(bundle_file)
    b.download(cache_dir=cache_dir,
               update=update)
    if not preexisting_pack:
        pack = b.gmkpack_create_pack(pack_type,
                                     compiler_label=compiler_label,
                                     compiler_flag=compiler_flag,
                                     homepack=homepack,
                                     rootpack=rootpack)
    else:
        packname = b.gmkpack_guess_pack_name(pack_type,
                                             compiler_label=compiler_label,
                                             compiler_flag=compiler_flag,
                                             homepack=homepack)
        pack = Pack(packname,
                    homepack=GmkpackTool.get_homepack(homepack))
        if clean_if_preexisting:
            pack.cleanpack()
    pack.bundle_populate(b)
    print("Pack successfully populated: " + pack.abspath)
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
    # preprocess args
    if isinstance(pack, six.string_types):
        pack = Pack(pack, preexisting=True, homepack=homepack)
    elif not isinstance(pack, Pack):
        raise PackError("**pack** argument must be a pack name or a Pack instance")
    programs = GmkpackTool.parse_programs(programs)
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

