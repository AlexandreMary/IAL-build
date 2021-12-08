#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python wrapping of *gmkpack*.
"""
from __future__ import print_function, absolute_import, unicode_literals, division

import six
import os
import re
import subprocess
import tarfile
import io
import shutil
from contextlib import contextmanager

from bronx.stdtypes.date import now

from .util import DirectoryFiltering, copy_files_in_cwd
from .config import (IAL_OFFICIAL_PACKS_re, IAL_OFFICIAL_TAGS_re, IAL_BRANCHES_re,
                     DEFAULT_PACK_COMPILER_FLAG)

#: No automatic export
__all__ = []

GCO_ROOTPACK = '/home/mf/dp/marp/martinezs/packs'
USUAL_BINARIES = ['masterodb', 'bator',
                  'ioassign', 'lfitools',
                  'pgd', 'prep',
                  'oovar', 'ootestvar',
                  ]

# The distinction is based on the component having a build system:
#         - integrated and plugged in gmkpack: package
#         - no build system, or not plugged in gmkpack: project
COMPONENTS_MAP = {'eckit':'hub/local/src/ecSDK',
                  'fckit':'hub/local/src/ecSDK',
                  'ecbuild':'hub/local/src/ecSDK',
                  # src/local
                  'arpifs':'src/local',
                  'ial':'src/local',
                  # __future__
                  #'atlas':'hub/local/src/Atlas',
                  #'surfex':'src/local/surfex',
                  #'oops':'src/local/oops_src'  # ???
                  }



class PackError(Exception):
    pass


class GmkpackTool(object):

    _default_branch_radical = 'main'
    _default_version_number = '00'
    _default_compiler_flag = DEFAULT_PACK_COMPILER_FLAG
    _OPTIONSPACK_re = re.compile('GMKFILE=(?P<gmkfile>.+)\s+<= -l (?P<label>\w+)\s+ -o (?P<flag>\w+)$')
    OFFICIAL_PACKS_re = IAL_OFFICIAL_PACKS_re

    @staticmethod
    def clean_env():
        vars_to_unset = ('GMK_USER_PACKNAME_STYLE', 'PACK_EXT', 'PACK_PREFIX')
        for k in vars_to_unset:
            if k in os.environ:
                print("unset $" + k)
                del os.environ[k]
        vars_to_set = {'GMK_RELEASE_CASE_SENSITIVE':'1', }
        for k, v in vars_to_set.items():
            print("export ${}={}".format(k, v))
            os.environ[k] = v

    @classmethod
    def commandline(cls,
                    arguments,
                    options=[],
                    silent=False):
        """
        Wrapper to gmkpack command.

        :param arguments: options with an argument to the command-line,
            to be passed as a dict, e.g. {'-l':'IMPIFC1801'}
        :param options: options without argument to the command-line,
            to be passed as a list, e.g. ['-a']
        :param silent: if True, hide gmkpack's stdout/stderr output
        """
        cls.clean_env()
        arguments_as_list = []
        for k, v in arguments.items():
            arguments_as_list.extend([k, v])
        arguments_as_list.extend(options)
        command = ['gmkpack',] + arguments_as_list
        print("Now running: " + ' '.join(command))
        if silent:
            with io.open(os.devnull, 'w') as devnull:
                r = subprocess.check_call(command, stdout=devnull, stderr=devnull)
        else:
            r = subprocess.check_call(command)
        return r

    @classmethod
    def scan_rootpacks(cls, directory):
        """Scan a 'rootpacks' directory, looking for official releases packs."""
        rootpacks = {}
        for p in os.listdir(directory):
            if not os.path.islink(os.path.join(directory, p)):
                m = cls.OFFICIAL_PACKS_re.match(p)
                if m:
                    rootpacks[p] = m.groupdict()
        return rootpacks

    @classmethod
    def find_matching_rootpacks(cls,
                                rootpacks_directory,
                                official_tag,
                                compiler_label=None,
                                compiler_flag=None):
        """Find rootpacks matching **official_tag**, with according label/flag if requested."""
        rootpacks = cls.scan_rootpacks(rootpacks_directory)
        compiler_label = cls.get_compiler_label(compiler_label)
        compiler_flag = cls.get_compiler_flag(compiler_flag)
        matching = {}
        for p in rootpacks.keys():
            if rootpacks[p]['radical'] == 'main':
                tag = 'CY{}'.format(rootpacks[p]['release'].upper())
            else:
                tag = 'CY{}_{}.{}'.format(rootpacks[p]['release'].upper(),
                                          rootpacks[p]['radical'],
                                          rootpacks[p]['version'])
            if tag == official_tag:
                if all([compiler_label in (None, rootpacks[p]['compiler_label']),
                        compiler_flag in (None, rootpacks[p]['compiler_flag'])]):
                    matching[p] = rootpacks[p]
        return matching

# ACCESSORS -------------------------------------------------------------------

    @staticmethod
    def get_homepack(homepack=None):
        """Get a HOMEPACK directory, from argument, $HOMEPACK, or $HOME/pack."""
        if homepack in (None, ''):
            homepack = os.environ.get('HOMEPACK')
            if homepack in (None, ''):
                homepack = os.path.join(os.environ.get('HOME'), 'pack')
        return homepack

    @staticmethod
    def get_rootpack(rootpack=None):
        """Get a ROOTPACK directory from argument, $ROOTPACK if defined, or None."""
        if rootpack in (None, ''):
            rootpack = os.environ.get('ROOTPACK')
        if rootpack in ('', None):
            raise ValueError("rootpack must be passed by argument or defined by env variable $ROOTPACK")
        return rootpack if rootpack != '' else None

    @classmethod
    def get_compiler_label(cls, compiler_label=None):
        """Get compiler label, either from argument (if not None) or from env var $GMKFILE."""
        if compiler_label in (None, ''):
            # get GMKFILE
            gmkfile = os.environ.get('GMKFILE')
            assert gmkfile not in (None, ''), "Cannot guess compiler label (-l): $GMKFILE is not set."
            # parse optionspack
            options = [f.strip()
                       for f in subprocess.check_output(['optionspack']).decode('utf-8').split('\n')
                       if f != '']
            for o in options:
                m = cls._OPTIONSPACK_re.match(o)
                if m and m.group('gmkfile').strip() == gmkfile:
                    compiler_label = m.group('label').strip()
                    break
        if compiler_label in (None, ''):
            raise ValueError("Compiler label not found, neither through env ($GMKFILE/optionspack) nor by argument")
        return compiler_label

    @classmethod
    def get_compiler_flag(cls, compiler_flag=None):
        """Get compiler flage, either from argument, $GMK_OPT or default value."""
        if compiler_flag in (None, ''):
            compiler_flag = os.environ.get('GMK_OPT')
            if compiler_flag in (None, ''):
                compiler_flag = cls._default_compiler_flag
        if compiler_flag in (None, ''):
            raise ValueError("Compiler flag not found, neither through env ($GMK_OPT) nor by argument")
        return compiler_flag

# getargs newway methods  -----------------------------------------------------

    @staticmethod
    def mainpack_getargs_from_IAL_git_ref(IAL_git_ref,
                                          IAL_repo_path=None):
        """
        Get necessary arguments for main pack from IAL_git_ref.

        :IAL_repo_path: required only if IAL_git_ref is not conventional
        """
        from .repositories import IALview
        is_a_tag = IAL_OFFICIAL_TAGS_re.match(IAL_git_ref)
        is_a_conventional_branch = IAL_BRANCHES_re.match(IAL_git_ref)
        if is_a_tag:
            gmk_release = is_a_tag.group('release')
            gmk_branch = is_a_tag.group('radical')
            gmk_version = is_a_tag.group('version')
            gmk_prefix = 'CY'
        elif is_a_conventional_branch:
            gmk_release = is_a_conventional_branch.group('release')
            gmk_branch = is_a_conventional_branch.group('radical')
            gmk_version = '00'
            gmk_prefix = is_a_conventional_branch.group('user') + '_CY'
        else:
            print("Warning: pack nomenclature will not be perfectly mapping git reference.")
            assert IAL_repo_path is not None, "IAL repository path is required because git ref is not conventional."
            ial = IALview(IAL_repo_path, IAL_git_ref)
            ancestor = IAL_OFFICIAL_TAGS_re.match(ial.latest_official_tagged_ancestor).groupdict()
            gmk_release = ancestor['release']
            gmk_branch = IAL_git_ref
            gmk_version = '00'
            gmk_prefix = '_upon'
        args = {'-r':gmk_release,
                '-b':gmk_branch,
                '-n':gmk_version,
                '-g':gmk_prefix}
        return args

    @classmethod
    def pack_getargs_others(cls,
                            compiler_label=None,
                            compiler_flag=None,
                            homepack=None):
        """Get necessary arguments for pack from argument or env variables."""
        return {'-o':cls.get_compiler_flag(compiler_flag),
                '-l':cls.get_compiler_label(compiler_label),
                '-h':cls.get_homepack(homepack)}

    @staticmethod
    def incrpack_getargs_from_IAL_git_ref(IAL_git_ref,
                                          IAL_repo_path):
        """Get necessary arguments for incr pack from IAL_git_ref."""
        from .repositories import IALview
        ial = IALview(IAL_repo_path, IAL_git_ref)
        # ancestor, for root pack
        ancestor = IAL_OFFICIAL_TAGS_re.match(ial.latest_official_tagged_ancestor)
        args = {'-r':ancestor.group('release')}
        if ancestor.group('radical'):
            args['-b'] = ancestor.group('radical')
            args['-v'] = ancestor.group('version')
        return args

    @classmethod
    def incrpack_getargs_packname(cls, IAL_git_ref, compiler_label=None, compiler_flag=None):
        """Get incr pack name (-u), built from ref and compiler."""
        return {'-u':'.'.join([IAL_git_ref,
                               cls.get_compiler_label(compiler_label),
                               cls.get_compiler_flag(compiler_flag)])}

    @classmethod
    def incrpack_getargs_from_root_pack(cls,
                                        args,
                                        IAL_git_ref,
                                        IAL_repo_path,
                                        rootpack=None,
                                        compiler_label=None,
                                        compiler_flag=None):
        """Get arguments linked to syntax of root pack."""
        from .repositories import IALview
        rootpack = cls.get_rootpack(rootpack)
        args['-f'] = rootpack
        # ancestor, for root pack
        ial = IALview(IAL_repo_path, IAL_git_ref)
        ancestor = ial.latest_official_tagged_ancestor
        matching = cls.find_matching_rootpacks(rootpack, ancestor, compiler_label, compiler_flag)
        if len(matching) == 1:
            actual_rootpack = matching[list(matching.keys())[0]]
            if actual_rootpack.get('prefix'):
                args['-g'] = actual_rootpack.get('prefix')
            if actual_rootpack.get('suffix'):
                args['-e'] = actual_rootpack.get('suffix')
            lower_case = actual_rootpack.get('release', '').islower()
            if lower_case:
                args['-r'] = args['-r'].lower()
            return args
        else:
            if len(matching) == 0:
                radic = "Could not find a pack in ROOTPACK={}"
            else:
                radic = "Too many packs in ROOTPACK={}"
            raise ValueError(" ".join([radic,
                                       "matching latest tagged ancestor ({}) of IAL_git_ref={}",
                                       "and compiler specifs label={}, flag={}."]).format(rootpack,
                                           ancestor, IAL_git_ref, compiler_label, compiler_flag))

    @classmethod
    def getargs(cls,
                pack_type,
                IAL_git_ref,
                IAL_repo_path=None,
                compiler_label=None,
                compiler_flag=None,
                homepack=None,
                rootpack=None):
        """
        Build args for incremental pack.

        :param pack_type: type of pack, among ('incr', 'main')
        :param IAL_git_ref: IAL git reference
        :param IAL_repo_path: IAL repository path
        :param compiler_label: Gmkpack's compiler label to be used
        :param compiler_flag: Gmkpack's compiler flag to be used
        :param homepack: directory in which to build pack
        :param rootpack: diretory in which to look for root pack
        """
        if pack_type == 'main':
            args = cls.mainpack_getargs_from_IAL_git_ref(IAL_git_ref, IAL_repo_path)
        elif pack_type == 'incr':
            args = cls.incrpack_getargs_from_IAL_git_ref(IAL_git_ref, IAL_repo_path)
            args.update(cls.incrpack_getargs_packname(IAL_git_ref,
                                                      compiler_label=compiler_label,
                                                      compiler_flag=compiler_flag))
            args.update(cls.incrpack_getargs_from_root_pack(args,
                                                            IAL_git_ref,
                                                            IAL_repo_path,
                                                            rootpack=rootpack,
                                                            compiler_label=compiler_label,
                                                            compiler_flag=compiler_flag))
        args.update(cls.pack_getargs_others(compiler_label=compiler_label,
                                            compiler_flag=compiler_flag,
                                            homepack=homepack))
        return args

# args oldway methods  --------------------------------------------------------

    @classmethod
    def args_for_incremental_commandline(cls,
                                         packname,
                                         initial_release,
                                         initial_branch=None,
                                         initial_branch_version=None,
                                         compiler_label=None,
                                         compiler_flag=None,
                                         rootpack=None,
                                         homepack=None):
        """Build the dict associating arguments to commandline."""
        args = {'-r':initial_release.replace('cy', '').replace('CY', ''),
                '-l':cls.get_compiler_label(compiler_label),
                '-o':cls.get_compiler_flag(compiler_flag),
                '-h':cls.get_homepack(homepack),
                '-u':packname}
        if initial_branch is not None:
            args['-b'] = initial_branch
            if initial_branch_version is not None:
                args['-v'] = initial_branch_version
        rootpack = cls.get_rootpack(rootpack)
        # rootpack and implications
        if rootpack is not None:
            args['-f'] = rootpack
        if rootpack == GCO_ROOTPACK:
            args['-g'] = 'cy'
            args['-e'] = '.pack'
            args['-r'] = args['-r'].lower()
        else:
            args['-g'] = 'CY'
        return args

    @classmethod
    def args_for_main_commandline(cls,
                                  initial_release,
                                  branch_radical,
                                  version_number,
                                  compiler_label=None,
                                  compiler_flag=None,
                                  prefix=None,
                                  homepack=None):
        """Build the dict associating arguments to commandline."""
        if branch_radical is None:
            branch_radical = cls._default_branch_radical
        if version_number is None:
            version_number = cls._default_version_number
        args = {'-r':initial_release.replace('cy', '').replace('CY', ''),
                '-b':branch_radical,
                '-o':cls.get_compiler_flag(compiler_flag),
                '-l':cls.get_compiler_label(compiler_label),
                '-h':cls.get_homepack(homepack),
                '-n':version_number}
        if prefix is not None:
            args['-g'] = prefix
        return args

# other methods ---------------------------------------------------------------

    @classmethod
    def args2packname(cls, args, pack_type):
        """Emulates gmkpack generation of pack name."""
        if pack_type == 'main':
            return '{}{}_{}.{}.{}.{}{}'.format(args.get('-g', ''), args['-r'], args['-b'],
                                               args['-n'], args['-l'], args['-o'],
                                               args.get('-e', ''))
        elif pack_type == 'incr':
            return args['-u']

    @classmethod
    def guess_pack_name(cls, IAL_git_ref, compiler_label, compiler_flag, pack_type,
                        IAL_repo_path=None):
        """
        Guess pack name given IAL git ref and compiler options.

       :param IAL_repo_path: is only necessary for main packs only if
            the **IAL_git_ref** happens not to be a conventional IAL name.
        """
        if pack_type == 'main':
            args = cls.getargs(pack_type,
                               IAL_git_ref,
                               IAL_repo_path=IAL_repo_path,
                               compiler_label=compiler_label,
                               compiler_flag=compiler_flag)
        elif pack_type == 'incr':
            args = cls.incrpack_getargs_packname(IAL_git_ref,
                                                 compiler_label,
                                                 compiler_flag)
        return cls.args2packname(args, pack_type)

# Pack Building methods -------------------------------------------------------

    @classmethod
    def new_incremental_pack(cls,
                             packname,
                             compiler_label,
                             initial_release,
                             initial_branch=None,
                             initial_branch_version=None,
                             compiler_flag=None,
                             rootpack=None,
                             homepack=None,
                             silent=False):
        """
        Create a new incremental pack.

        :param packname: name of the pack
        :param compiler_label: gmkpack compiler label
        :param initial_release: release to start from
        :param initial_branch: branch on release to start from
        :param initial_branch_version: version number on the branch to start from
        :param compiler_flag: gmkpack compiler_flag
        :param rootpack: where to look for pack to start from (option -f of gmkpack)
        :param homepack: home directory for packs
        :param silent: to mute gmkpack
        """
        args = cls.args_for_incremental_commandline(packname,
                                                    initial_release=initial_release,
                                                    initial_branch=initial_branch,
                                                    initial_branch_version=initial_branch_version,
                                                    compiler_label=compiler_label,
                                                    compiler_flag=compiler_flag,
                                                    rootpack=rootpack,
                                                    homepack=homepack)
        return cls.create_pack_from_args(args, 'main', silent=silent)

    @classmethod
    def new_main_pack(cls,
                      initial_release,
                      branch_radical,
                      version_number,
                      compiler_label=None,
                      compiler_flag=None,
                      prefix=None,
                      homepack=None,
                      silent=False):
        """
        Create a new incremental pack.

        :param initial_release: release
        :param branch_radical: "branch" on release (radical in the pack name)
        :param version_number: version number on the "branch"
        :param compiler_label: gmkpack reference compiler version
        :param compiler_flag: gmkpack compiler_flag
        :param prefix: prefix to the pack name
        :param homepack: home directory for packs
        :param silent: to mute gmkpack
        """
        args = cls.args_for_main_commandline(initial_release,
                                             branch_radical,
                                             version_number,
                                             compiler_label=compiler_label,
                                             compiler_flag=compiler_flag,
                                             prefix=prefix,
                                             homepack=homepack)
        return cls.create_pack_from_args(args, 'main', silent=silent)

    @classmethod
    def create_pack_from_args(cls, args, pack_type,
                              silent=False):
        packname = cls.args2packname(args, pack_type)
        pack = Pack(packname, preexisting=False, homepack=args.get('-h'))
        if os.path.exists(pack.abspath):
            raise PackError('Pack already exists, cannot create: {}'.format(pack.abspath))
        options = ['-a', '-K'] if pack_type == 'main' else []
        cls.commandline(args, options, silent=silent)
        return pack


class Pack(object):

    def __init__(self, packname, preexisting=True, homepack=None):
        """
        Create Pack object from the **packname**.
        """
        self.packname = packname
        if homepack in (None, ''):
            homepack = GmkpackTool.get_homepack()
        self.homepack = homepack
        self.abspath = os.path.join(self.homepack, packname)
        self._local = os.path.join(self.abspath, 'src', 'local')
        self._hub_local_src = os.path.join(self.abspath, 'hub', 'local', 'src')
        self._bin = os.path.join(self.abspath, 'bin')
        if not preexisting and os.path.exists(self.abspath):
            raise PackError("Pack already exists, while *preexisting* is False ({}).".format(self.abspath))
        if preexisting and not os.path.exists(self.abspath):
            raise PackError("Pack is supposed to preexist, while it doesn't ({}).".format(self.abspath))

    @property
    def is_incremental(self):
        """Is the pack incremental ? (vs. main)"""
        return '-a' not in self.genesis_options

    @contextmanager
    def _cd_local(self, subdir=None):
        """Context: in self._local"""
        owd = os.getcwd()
        if subdir is None:
            loc = self._local
        else:
            loc = os.path.join(self._local, subdir)
        try:
            os.chdir(loc)
            yield loc
        finally:
            os.chdir(owd)

    @property
    def genesis(self):
        """Read pack/.genesis file and return it."""
        genesis = os.path.join(self.abspath, '.genesis')
        with io.open(genesis, 'r') as g:
            genesis = g.readline().strip()
        return genesis

    def _genesis_parse(self):
        genesis = self.genesis.split()[1:]
        arguments = {}
        options = []
        for i, arg in enumerate(genesis):
            if arg.startswith('-'):
                if i == len(genesis) - 1:  # last one, is an option
                    options.append(arg)
                elif genesis[i + 1].startswith('-'):  # next starts with '-', is an option
                    options.append(arg)
                else:
                    arguments[arg] = genesis[i + 1]
        if '-g' in arguments and arguments['-r'].startswith(arguments['-g']):
            arguments['-r'] = arguments['-r'][len(arguments['-g']):]  # FIXME: workaround gmkpack weirdery
        return arguments, options

    @property
    def genesis_arguments(self):
        """Return arguments (e.g. -r 47t1) of pack creation as a dict."""
        return self._genesis_parse()[0]

    @property
    def genesis_options(self):
        """Return options (e.g. -a) of pack creation as a list."""
        return self._genesis_parse()[1]

    @property
    def release(self):
        """Lastest ancestor main release to the pack."""
        return 'CY' + self.genesis_arguments['-r'].upper().replace('CY', '')  # CY might be or not be here

    @property
    def tag_of_latest_official_ancestor(self):
        """Tag of latest official ancestor."""
        assert self.is_incremental
        args = self.genesis_arguments
        tag = self.release
        if args['-b'] != 'main':
            tag += '_{}.{}'.format(args['-b'], args['-v'])
        return tag

    # Methods around *ics_* compilation scripts --------------------------------

    def ics_path_for(self, program):
        """Path of the compilation script for **program**."""
        return os.path.join(self.abspath, 'ics_' + program.lower())

    def ics_remove(self, program):
        """Remove the compilation script for **program**."""
        if self.ics_available_for(program):
            os.remove(self.ics_path_for(program))

    def ics_available_for(self, program):
        """Whether the compilation script exists for **program**."""
        return os.path.exists(self.ics_path_for(program))

    def ics_build_for(self, program, silent=False,
                      GMK_THREADS=32,
                      Ofrt=4,
                      partition=None,
                      no_compilation=False,
                      no_libs_update=False):
        """Build the 'ics_*' script for **program**."""
        args = self.genesis_arguments
        args.update({'-p':program.lower()})
        if os.path.exists(self.ics_path_for(program)):
            os.remove(self.ics_path_for(program))
        args.update({'-h':self.homepack})
        # build ics
        GmkpackTool.commandline(args, self.genesis_options, silent=silent)
        # modify number of threads
        pattern = 'export GMK_THREADS=(\d+)'
        self._ics_modify(program,
                         re.compile(pattern),
                         pattern.replace('(\d+)', str(GMK_THREADS)))
        # modify optimization level
        pattern = 'Ofrt=(\d)'
        self._ics_modify(program,
                         re.compile(pattern),
                         pattern.replace('(\d)', str(Ofrt)))
        # modify partition
        if partition is not None:
            pattern = '\#SBATCH -p (.+)'
            self._ics_modify(program,
                             re.compile(pattern),
                             pattern.replace('(.+)', partition).replace('\#', '#'))
        # switch off compilation
        if no_compilation:
            pattern = 'export ICS_ICFMODE=(.+)'
            self._ics_modify(program,
                             re.compile(pattern),
                             pattern.replace('(.+)', 'off'))
        # switch off libs update
        if no_libs_update:
            pattern = 'export ICS_UPDLIBS=(.+)'
            self._ics_modify(program,
                             re.compile(pattern),
                             pattern.replace('(.+)', 'off'))
        # ignore files
        if os.path.exists(self._ignore_at_compiletime_filepath):
            self.ics_ignore_files(program, self._ignore_at_compiletime_filepath)

    def ics_ignore_files(self, program, list_of_files):
        """
        Add **list_of_files** to be ignored to ics_program.

        :param list_of_files: a list of filenames,
            or a filename of a file containing the list of filenames
        """

        if isinstance(list_of_files, six.string_types):  # filename of a file containing list of files to ignore
            pattern = 'end_of_ignored_files'
            self._ics_insert(program, pattern,
                             ['cat {} >> $GMKWRKDIR/.ignored_files'.format(list_of_files)],
                             offset=1)
        else:  # a python list of files to ignore
            pattern = 'cat <<end_of_ignored_files> $GMKWRKDIR/.ignored_files'
            with io.open(list_of_files, 'r') as f:
                list_of_files = [l.strip() for l in f.readlines()]
            self._ics_insert(program, pattern, list_of_files, offset=1)

    @property
    def ics_available(self):
        """Lists the available ics_ compilation scripts."""
        return sorted([f for f in os.listdir(self.abspath)
                       if f.startswith('ics_')])

    def _ics_read(self, program):
        with io.open(self.ics_path_for(program), 'r') as f:
            ics = [line.rstrip() for line in f.readlines()]
        return ics

    def _ics_write(self, program, ics):
        with io.open(self.ics_path_for(program), 'w') as f:
            for line in ics:
                f.write(line + '\n')

    def _ics_modify(self, program, pattern, replacement):
        """
        Modify the ics_program script.

        :param pattern: a re.compile() pattern or a string;
            if line matches, replaced by **replacement**
        :param replacement: replacement line
        """
        ics = self._ics_read(program)
        for i, line in enumerate(ics):
            try:
                ok = line == pattern or pattern.match(line)
            except AttributeError:
                ok = False
            if ok:
                print("ial_build.pygmkpack.Pack._ics_modify():", ics[i], '=>', replacement)
                ics[i] = replacement
                break
        self._ics_write(program, ics)

    def _ics_insert(self, program, pattern, lines, offset=1):
        """
        Insert **lines** in ics_program after/before **pattern**.

        :param pattern: a re.compile() pattern or a string
        :param offset: 0 to insert before, 1 to insert after
        """
        ics = self._ics_read(program)
        for i, line in enumerate(ics):
            try:
                ok = line == pattern or pattern.match(line)
            except AttributeError:
                ok = False
            if ok:
                break
        for l in lines[::-1]:
            ics.insert(i + offset, l)
        self._ics_write(program, ics)

    # Populate pack ------------------------------------------------------------

    @property
    def origin_filepath(self):
        """File in which to find info about origin of the pack."""
        return os.path.join(self.abspath, '.pygmkpack.populated')

    def populate_from_tar(self, tar):
        """Populate the incremental pack with the contents of a **tar** file."""
        with tarfile.open(tar, 'r') as t:
            t.extractall(path=self._local)

    def populate_from_list_of_files_in_dir(self, list_of_files, directory, subdir=None):
        """
        Populate the incremental pack with the **list_of_files** from a given **directory**.

        :param subdir: if given, populate in src/local/subdir/
        """
        directory_abspath = os.path.abspath(directory)
        with self._cd_local(subdir=subdir):
            copy_files_in_cwd(list_of_files, directory_abspath)

    # DEPRECATED:migrate to bundle
    def populate_from_IALview_as_main(self, view,
                                      populate_filter_file=None,
                                      link_filter_file=None):
        """
        Populate main pack with contents from a IALview.

        :param populate_filter_file: file in which to read the files to be
            filtered at populate time.
            Special values:
            '__inconfig__' will read according file in config of ial_build package;
            '__inrepo__' will read according file in Git repository
        :param link_filter_file: file in which to read the files to be
            filtered at link time.
            Special values:
            '__inconfig__' will read according file in config of ial_build package;
            '__inrepo__' will read according file in Git repository
        """
        from .repositories import IALview
        assert isinstance(view, IALview)
        self._populate_from_repo_in_bulk(view.repository,
                                         populate_filter_file=populate_filter_file,
                                         link_filter_file=link_filter_file)
        self.write_view_info(view)

    # DEPRECATED:migrate to bundle
    def populate_from_IALview_as_incremental(self, view, start_ref=None):
        """
        Populate as incremental pack with contents from a IALview.

        :param view: a IALview instance
        :param start_ref: increment of modification starts from this ref.
            If None, starts from latest official tagged ancestor.
        """
        from .repositories import IALview, GitError
        assert isinstance(view, IALview)
        if start_ref is None:
            self._assert_IALview_compatibility(view)
            touched_files = view.touched_files_since_latest_official_tagged_ancestor
        else:
            touched_files = view.touched_files_since(start_ref)
        if len(view.git_proxy.touched_since_last_commit) > 0:
            print("! Note:  non-committed files in the view are exported to the pack.")
        # files to be copied
        files_to_copy = []
        for k in ('A', 'M', 'T'):
            files_to_copy.extend(list(touched_files.get(k, [])))
        for k in ('R', 'C'):
            files_to_copy.extend([f[1] for f in touched_files.get(k, [])])  # new name of renamed or copied files
        self.populate_from_list_of_files_in_dir(files_to_copy, view.repository)
        # files to be ignored/deleted
        files_to_delete = list(touched_files.get('D', []))
        files_to_delete.extend([f[0] for f in touched_files.get('R', [])])  # original name of renamed files
        self.write_ignored_files_at_compiletime(files_to_delete)
        # files of unknown status
        for k in ('U', 'X', 'B'):
            if k in touched_files:
                raise GitError("Don't know what to do with files which Git status is: " + k)
        self.write_view_info(view)

    # DEPRECATED:migrate to bundle
    def populate_hub(self, latest_main_release):
        """
        Populate hub packages in main pack.

        WARNING: temporary solution before 'bundle' implementation !
        """
        from .config import GMKPACK_HUB_PACKAGES
        from .util import host_name
        msg = "Populating vendor packages in pack's hub:"
        print(msg + "\n" + "-" * len(msg))
        for package, properties in GMKPACK_HUB_PACKAGES.items():
            rootdir = properties[host_name()]
            version = properties[latest_main_release]
            project = properties['project']
            print("Package: '{}/{}' (v{}) from {}".format(project, package, version, rootdir))
            pkg_src = os.path.join(rootdir, package, version)
            pkg_dst = os.path.join(self._hub_local_src, project, package)
            shutil.copytree(pkg_src, pkg_dst, symlinks=True)
        print("-" * len(msg))

    # DEPRECATED:migrate to bundle
    def write_view_info(self, view):
        """Write view.info into self.origin_filepath."""
        openmode = 'a' if os.path.exists(self.origin_filepath) else 'w'
        with io.open(self.origin_filepath, openmode) as f:
            view.info(out=f)

    # DEPRECATED:migrate to bundle
    def _assert_IALview_compatibility(self, view):
        """Assert that view and pack have the same original node (ancestor)."""
        branch_ancestor_info = view.latest_official_branch_from_main_release
        args = self.genesis_arguments
        pack_release = self.release
        assert branch_ancestor_info['release'] == pack_release, \
            "release: (view)={} vs. (pack)={}".format(branch_ancestor_info['release'],
                                                      pack_release)
        if branch_ancestor_info['radical'] is not None:
            assert branch_ancestor_info['radical'] == args['-b'], \
                "official view: (view)={} vs. (pack)={}".format(branch_ancestor_info['radical'],
                                                                    args['-b'])
            assert branch_ancestor_info['version'] == args['-v'], \
                "official view version: (view)={} vs. (pack)={}".format(branch_ancestor_info['version'],
                                                                            args['-v'])
        else:
            assert args['-b'] == 'main'

    def _populate_from_repo_in_bulk(self,
                                    repository,
                                    subdir=None,
                                    populate_filter_file=None,
                                    link_filter_file=None):
        """
        Populate a main pack src/local/ with the contents of a repo.

        :param subdir: if given, populate in src/local/{subdir}/
        """
        # prepare populate filter
        pop_filter_list = self._read_filter_list('populate',
                                                 populate_filter_file,
                                                 repository)
        for i, f in enumerate(pop_filter_list):
            if not os.path.isabs(f):
                pop_filter_list[i] = os.path.join(repository, f)
        # populate
        print("\nSubprojects:")
        for f in sorted(os.listdir(repository)):
            f_src = os.path.join(repository, f)
            if subdir is None:
                f_dst = os.path.join(self._local, f)
            else:
                f_dst = os.path.join(self._local, subdir, f)
            if f_src in pop_filter_list and os.path.isdir(f_src):
                print("({} is filtered out)".format(f))
            else:
                if os.path.isdir(f_src):  # actual subproject
                    print(f)
                    subproject = DirectoryFiltering(f_src, pop_filter_list)
                    subproject.copytree(f_dst, symlinks=True)  # TODO: rsync instead, to recompile only modified files
                else:
                    shutil.copy(f_src, f_dst)  # single file
        # link filter
        link_filter_list = self._read_filter_list('link',
                                                  link_filter_file,
                                                  repository)
        self.set_ignored_files_at_linktime(link_filter_list)

    # Populate from bundle -----------------------------------------------------

    def bundle_populate_component(self,
                                  component,
                                  bundle,
                                  populate_filter_file=None,
                                  link_filter_file=None):
        """
        Populate src/local in incr pack from bundle.

        :param bundle: the ial_build.bundle.IALBundle object.
        :param populate_filter_file: file in which to read the files to be
            filtered at populate time.
            Special values:
            '__inconfig__' will read according file in config of ial_build package;
            '__inrepo__' will read according file in Git repo
        :param link_filter_file: file in which to read the files to be
            filtered at link time.
            Special values:
            '__inconfig__' will read according file in config of ial_build package;
            '__inrepo__' will read according file in Git repo
        """
        config = bundle.projects[component]
        pkg_dst = self._bundle_component_destination(component, config)
        repository = bundle.local_project_repo(component)
        if pkg_dst.startswith('hub'):
            # packages auto-compiled, in hub
            print("Hub Package: '{}' ({}) from repo: {} via cache: {}".format(component,
                                                                              config['version'],
                                                                              config['git'],
                                                                              repository))
            if self.is_incremental:
                print("!-> Incremental hub packages is currently not an available feature: populated in bulk")
            pkg_dst = os.path.join(self.abspath, pkg_dst, component)
            shutil.copytree(repository, pkg_dst, symlinks=True)
        elif pkg_dst.startswith('src/local'):
            # components to be compiled with gmkpack, in src/local
            print("Component: '{}' ({}) from repo: {} via cache: {}".format(component,
                                                                            config['version'],
                                                                            config['git'],
                                                                            repository))
            subdir = os.path.split(pkg_dst)
            if len(subdir) > 2:
                subdir = subdir[2]
            else:
                subdir = None
            if not self.is_incremental or self.initial_version_of_component(component) is None:
                # main pack, or not able to determine an increment: bulk
                if self.is_incremental:
                    print("! Could not find initial version of component '{}'".format(component),
                          "in root pack: populate in bulk")
                self._populate_from_repo_in_bulk(repository,
                                                 subdir=subdir,
                                                 populate_filter_file=populate_filter_file,
                                                 link_filter_file=link_filter_file)
            else:
                # incremental pack
                self._populate_from_repo_as_incremental_component(repository,
                                                                  self.initial_version_of_component(component),
                                                                  subdir=subdir)

    def initial_version_of_component(self, component):
        """
        In an incremenal pack, guess the initial version of **component** in the root pack.
        """
        if component.lower() in ('arpifs', 'ial'):
            version = self.tag_of_latest_official_ancestor
        # elif component == ...
        # implement here whenever src/local components are introduced in bundle
        else:
            version = None  # this will turn component to be populated in bulk rather than as increment
        return version

    def _populate_from_repo_as_incremental_component(self,
                                                     repository,
                                                     initial_version,
                                                     populating_version='HEAD',
                                                     subdir=None):
        """
        Populate the incremental pack with the diff between **initial_version** and **populating_version**
        from **repository**.

        :param subdir: if given, populate in src/local/subdir/ (otherwise src/local/)
        """
        from .repositories import GitProxy
        repo = GitProxy(repository)
        touched_files = repo.touched_between(initial_version, populating_version)
        # files to be copied
        files_to_copy = []
        for k in ('A', 'M', 'T'):
            files_to_copy.extend(list(touched_files.get(k, [])))
        for k in ('R', 'C'):
            files_to_copy.extend([f[1] for f in touched_files.get(k, [])])  # new name of renamed or copied files
        self.populate_from_list_of_files_in_dir(files_to_copy, repository, subdir=subdir)
        # files to be ignored/deleted
        files_to_delete = list(touched_files.get('D', []))
        files_to_delete.extend([f[0] for f in touched_files.get('R', [])])  # original name of renamed files
        self.write_ignored_files_at_compiletime(files_to_delete)
        # files of unknown status
        for k in ('U', 'X', 'B'):
            if k in touched_files:
                raise GitError("Don't know what to do with files which Git status is: " + k)

    def bundle_populate(self,
                        bundle,
                        populate_filter_file=None,
                        link_filter_file=None):
        """
        Populate pack from bundle.

        :param bundle: the ial_build.bundle.IALBundle object.
        :param populate_filter_file: file in which to read the files to be
            filtered at populate time.
            Special values:
            '__inconfig__' will read according file in config of ial_build package;
            '__inrepo__' will read according file in Git repo
        :param link_filter_file: file in which to read the files to be
            filtered at link time.
            Special values:
            '__inconfig__' will read according file in config of ial_build package;
            '__inrepo__' will read according file in Git repo
        """
        hub_components = {component:config for component, config in bundle.projects.items()
                          if self._bundle_component_destination(component, config).startswith('hub')}
        gmkpack_components = {component:config for component, config in bundle.projects.items()
                              if self._bundle_component_destination(component, config).startswith('src/local')}
        # start with hub:
        msg = "Populating components in pack's hub:"
        print("\n" + msg + "\n" + "-" * len(msg))
        for component, config in hub_components.items():
            self.bundle_populate_component(component,
                                           bundle,
                                           populate_filter_file=populate_filter_file,
                                           link_filter_file=link_filter_file)
        # then src/local components:
        msg = "Populating components in pack's src/local:"
        print("\n" + msg + "\n" + "-" * len(msg))
        for component, config in gmkpack_components.items():
            self.bundle_populate_component(component,
                                           bundle,
                                           populate_filter_file=populate_filter_file,
                                           link_filter_file=link_filter_file)
        # log in pack
        self._bundle_write_properties(bundle.projects)

    # FIXME: clean !
    def bundle_populate_mainpack(self,
                                 bundle,
                                 populate_filter_file=None,
                                 link_filter_file=None):
        """
        Populate src/local in main pack from bundle.

        :param bundle: the ial_build.bundle.IALBundle object.
        :param populate_filter_file: file in which to read the files to be
            filtered at populate time.
            Special values:
            '__inconfig__' will read according file in config of ial_build package;
            '__inrepo__' will read according file in Git repo
        :param link_filter_file: file in which to read the files to be
            filtered at link time.
            Special values:
            '__inconfig__' will read according file in config of ial_build package;
            '__inrepo__' will read according file in Git repo
        """
        assert not self.is_incremental
        # hub packages
        self._bundle_populate_hub(bundle)
        # src/local
        msg = "Populating components in pack's src/local:"
        print("\n" + msg + "\n" + "-" * len(msg))
        for component, config in bundle.projects.items():
            pkg_dst = self._bundle_component_destination(component, config)
            if pkg_dst.startswith('src/local'):
                repository = bundle.local_project_repo(component)
                subdir = config.get('copy_to_subdirectory', None)
                print("Package: '{}' ({}) from repo: {} via cache: {}".format(component,
                                                                              config['version'],
                                                                              config['git'],
                                                                              repository))
                self._populate_from_repo_in_bulk(repository,
                                                 subdir=subdir,
                                                 populate_filter_file=populate_filter_file,
                                                 link_filter_file=link_filter_file)
        # log in pack
        self._bundle_write_properties(bundle.projects)

    # FIXME: clean !
    def bundle_populate_incrpack(self,
                                 bundle,
                                 populate_filter_file=None,
                                 link_filter_file=None):
        """
        Populate src/local in incr pack from bundle.

        :param bundle: the ial_build.bundle.IALBundle object.
        :param populate_filter_file: file in which to read the files to be
            filtered at populate time.
            Special values:
            '__inconfig__' will read according file in config of ial_build package;
            '__inrepo__' will read according file in Git repo
        :param link_filter_file: file in which to read the files to be
            filtered at link time.
            Special values:
            '__inconfig__' will read according file in config of ial_build package;
            '__inrepo__' will read according file in Git repo
        """
        assert self.is_incremental
        # hub packages: TODO: should we ? or check that it corresponds to root pack
        self._bundle_populate_hub(bundle)
        # src/local
        msg = "Populating components in pack's src/local:"
        print("\n" + msg + "\n" + "-" * len(msg))
        for component, in bundle.projects.items():
            pkg_dst = self._bundle_component_destination(component, config)
            if pkg_dst.startswith('src/local'):
                version_in_main = self._version_of_component_in_main(component)
                repository = bundle.local_project_repo(component)
                subdir = config.get('copy_to_subdirectory', None)
                print("Package: '{}' ({}) from repo: {} via cache: {}".format(component,
                                                                              config['version'],
                                                                              config['git'],
                                                                              repository))
                if version_in_main is not None:
                    list_of_files = bundle.git_diff(component, version_in_main)
                    self._populate_from_repo_as_incremental_component(component,
                                                                      bundle.local_project_repo(component),
                                                                      start_version=version_in_main)
                else:
                    # populate in bulk
                    self._populate_from_repo_in_bulk(repository,
                                                     subdir=subdir,
                                                     populate_filter_file=populate_filter_file,
                                                     link_filter_file=link_filter_file)
        # TODO:
        # log in pack
        self._bundle_write_properties(projects)

    # FIXME: clean !
    def _bundle_populate_hub(self, bundle):
        """
        Populate hub packages in main pack from bundle in cache_dir.

        :param bundle: the ial_build.bundle.IALBundle object.
        """
        msg = "Populating vendor packages in pack's hub:"
        print("\n" + msg + "\n" + "-" * len(msg))
        for project, config in bundle.projects.items():
            pkg_dst = self._bundle_component_destination(project, config)
            if pkg_dst.startswith('hub'):
                pkg_src = os.path.join(bundle.downloaded_to, project)
                pkg_dst = os.path.join(self.abspath, pkg_dst, project)
                print("Package: '{}' ({}) from repo: {} via cache: {}".format(project,
                                                                              config['version'],
                                                                              config['git'],
                                                                              pkg_src))
                shutil.copytree(pkg_src, pkg_dst, symlinks=True)

    def _bundle_component_destination(self, component, config):
        """
        Distinction between 'projects' (in src/local) and 'packages' (in hub),
        as specified in bundle (attribute 'gmkpack') or parameterized.

        The distinction is based on the component having a build system:
        - integrated and plugged in gmkpack: package
        - no build system, or not plugged in gmkpack: project
        """
        destination = config.get('gmkpack', COMPONENTS_MAP.get(component.lower(), None))
        assert destination is not None, ' '.join(["Destination of component '{}' within gmkpack is unknown,",
                                                  "please indicate in bundle file through attribute 'gmkpack',",
                                                  "e.g. gmkpack = src/local/oops or",
                                                  "hub/local/src/ecSDK"]).format(component)
        return destination

    def _bundle_write_properties(self, projects):
        """Write info into self.origin_filepath."""
        openmode = 'a' if os.path.exists(self.origin_filepath) else 'w'
        with io.open(self.origin_filepath, openmode) as f:
            f.write("\n{} --- populate from bundle successful with:\n".format(now()))
            for project, config in projects.items():
                f.write("* {}\n".format(project))
                f.write("    version: {}\n".format(config['version']))
                f.write("    from remote git: {}\n".format(config['git']))

    # Filters ------------------------------------------------------------------

    def _ignore_basename4(self, step):
        """Get basename of ignore files for a given **step**."""
        return 'pygmkpack.ignore4{}'.format(step)

    def _ignore_filepath4(self, step, where, repository=None):
        """
        Get filepath of ignore files for a given **step**,
        in 'config' or 'view'.
        """
        if where == '__inconfig__':
            dirpath = os.path.join(os.path.dirname(__file__), 'config')
            basename = '.'.join([self._ignore_basename4(step), self.release])
            filepath = os.path.join(dirpath, basename)
            if not os.path.exists(filepath):
                basename = self._ignore_basename4(step)
        elif where == '__inrepo__':
            assert repository is not None, "Argument **repository** is required if **where** is '__inrepo__'."
            dirpath = repository
            basename = self._ignore_basename4(step)
        return os.path.join(dirpath, basename)

    @property
    def _ignore_at_compiletime_filepath(self):
        """File in which to find the files to be ignored at compilation time."""
        return os.path.join(self.abspath, self._ignore_basename4('compile'))

    def _read_filter_list(self, step, filter_file, repository=None):
        """Read filter list from file."""
        if filter_file in ('__inconfig__', '__inrepo__'):
            f = self._ignore_filepath4(step, filter_file, repository)
            if os.path.exists(f):
                filter_file = f
            else:
                print("(Filter file '{}' does not exist ! Ignore.)".format(f))
                filter_file = None
        if filter_file is not None:
            with io.open(filter_file, 'r') as ff:
                filter_list = [f.strip() for f in ff.readlines()
                               if (not f.startswith('#') and f.strip() != '')]
            print("\nRead filter for {} time from {}:".format(step, filter_file))
            print("Filter contents:")
            for f in filter_list:
                print(f)
        else:
            filter_list = []
        return filter_list

    def set_ignored_files_at_linktime(self, list_of_ignored_symbols):
        """Set symbols to be ignored in src/unsxref/verbose."""
        if isinstance(list_of_ignored_symbols, six.string_types):
            with io.open(list_of_ignored_symbols, 'r') as f:
                list_of_ignored_symbols = [l.strip() for l in f.readlines()]
        for s in list_of_ignored_symbols:
            symbol_path = os.path.join(self.abspath, 'src', 'unsxref', 'verbose', s)
            with io.open(symbol_path, 'a'):
                os.utime(symbol_path, None)

    def write_ignored_files_at_compiletime(self, list_of_files):
        """Write files to be ignored in a dedicated file."""
        if isinstance(list_of_files, six.string_types):  # already a file containing filenames: copy
            shutil.copyfile(list_of_files, self._ignore_at_compiletime_filepath)
        else:
            with io.open(self._ignore_at_compiletime_filepath, 'w') as f:  # a python list
                for l in list_of_files:
                    f.write(l + '\n')
        if 'ics_' in self.ics_available:
            self.ics_ignore_files('', self._ignore_at_compiletime_filepath)

    # From pack to branch -------------------------------------------------------
    @property
    def _packname2branchname(self):
        args = self.genesis_arguments  # TODO: main pack case
        packname = self.packname
        # prune reference compiler version and compiler options
        suffix = '.{}.{}'.format(args['-l'], args['-o'])
        if packname.endswith(suffix):
            packname = packname.replace(suffix, '')
        # try to identify user and release
        _re_branch = re.compile('{}_{}_(.+)'.format(os.getlogin(), self.release))
        if _re_branch.match(packname):
            branchname = packname
        else:
            branchname = '_'.join([os.getlogin(), self.release, packname])
        return branchname

    def save_as_IAL_branch(self, repository,
                           files_to_delete=[],
                           branchname=None,
                           preexisting_branch=False,
                           commit_message=None,
                           ask_confirmation=False,
                           register_in_GCOdb=False):
        """
        Save the contents of the pack into an IAL Branch.

        :param files_to_delete: either the filename of a file containing
            the list of files to ignore, or directly a list of files to delete
            in branch
        :param branchname: if None, generated from pack options as:
            <logname>_<release>_<packname>
        :param preexisting_branch: whether the branch already exists in the repository
        :param commit_message: if not None, activate committing the modifications
            after populating the branch with given commit message
        :param ask_confirmation: ask for confirmation about the repo/branch
            before actually creating branch and/or populating
        :param register_in_GCOdb: to register the branch in GCO database
        """
        from .repositories import IALview
        if not self.is_incremental:
            raise NotImplementedError("Populating branch from a main pack.")
        # guess branch name
        if branchname is None:
            branchname = self._packname2branchname
        touched_files = self.scanpack()
        if isinstance(files_to_delete, six.string_types):
            with io.open(files_to_delete, 'r') as f:
                files_to_delete = [file.strip() for file in f.readlines()]
        # printings
        print("Files modified or added:")
        for f in touched_files:
            print(f)
        print("-" * 80)
        if len(files_to_delete) > 0:
            print("Files to be deleted from repo:")
            for f in files_to_delete:
                print(f)
            print("-" * 80)
        if preexisting_branch:
            print("About to populate preexisting branch: '{}'".format(branchname))
        else:
            print("About to create & populate branch: '{}'".format(branchname))
            print("Starting from tag: {}".format(self.tag_of_latest_official_ancestor))
            print("In repository: {}".format(repository))
        if commit_message is not None:
            print("And commit with message: '{}'".format(commit_message))
        if ask_confirmation:
            ok = six.moves.input("Everything OK ? [y/n] ")
            if ok == 'n':
                print("Confirmation cancelled: exit.")
                exit()
            elif ok != 'y':
                print("Please answer by 'y' or 'n'. Exit.")
                exit()
        # now checkout branch
        if preexisting_branch:
            branch = IALview(repository, branchname)
        else:
            branch = IALview(repository, branchname,
                              new_branch=True,
                              start_ref=self.tag_of_latest_official_ancestor,
                              register_in_GCOdb=register_in_GCOdb)
        # copy modified/added files
        with branch.git_proxy.cd_repo():
            copy_files_in_cwd(touched_files, self._local)
        # remove files to be so
        assert isinstance(files_to_delete, list)
        for f in files_to_delete:
            branch.git_proxy.delete_file(f)
        print("=> Pack: '{}' saved as branch: '{}' in repository: {}".format(
            self.packname, branch.branch_name, repository))
        # commit  TOBECHECKED:
        if commit_message is not None:
            branch.git_proxy.stage(touched_files)
            branch.git_proxy.commit(commit_message, add=True)
            #print("Committed: {}".format(commit))
        else:
            print("Changes are not commited: cf. 'git status'")
        return branch

    # Executables --------------------------------------------------------------

    @property
    def available_executables(self):
        """Lists the available executables."""
        return sorted(os.listdir(self._bin))

    def executable_ok(self, program):
        """Check that **program** executable has been made."""
        bins = os.listdir(self._bin)
        return program.lower() in bins or program.upper() in bins

    # Compilation --------------------------------------------------------------

    def compile(self, program, silent=False, clean_before=False, fatal=True):
        """Run interactively the ics_ compilation script for **program**"""
        assert os.path.exists(self.ics_path_for(program))
        cmd = [self.ics_path_for(program),]
        if clean_before:
            self.cleanpack()
        try:
            if silent:
                logdir = os.path.join(self.abspath, 'log')
                if not os.path.exists(logdir):
                    os.makedirs(logdir)
                if program == '':
                    outname = os.path.join(logdir,
                                           '.'.join(['_',
                                                     now().stdvortex]))
                else:
                    outname = os.path.join(logdir,
                                           '.'.join([program.lower(),
                                                     now().stdvortex]))
                with io.open(outname, 'w') as f:
                    ok = subprocess.check_call(cmd, stdout=f, stderr=f)
            else:
                outname = None
                ok = subprocess.check_call(cmd)
        except Exception:
            if fatal:
                raise
            else:
                ok = False
        else:
            ok = True if int(ok) == 0 else False
            if program != '':
                ok = self.executable_ok(program)
            if fatal and not ok:
                if program == '':
                    message = "Compilation failed."
                else:
                    message = "Build of {} failed.".format(program)
                if outname is not None:
                    message += " Output: " + outname
                raise PackError(message)
        report = {'OK':ok,
                  'Output':outname}
        return report

    def compile_all_programs(self, silent=False):
        """Run interactively the ics_ compilation script for **program**"""
        for program in [s.replace('ics_', '') for s in self.ics_available]:
            print("Start compilation of {}...".format(program))
            r = self.compile(program, silent=silent)
            print(r)
            print("...ended.")

    def compile_batch(self, program, batch_scheduler):
        """
        Run in batch the ics_ compilation script for **program**, using
        **batch_scheduler**
        """
        raise NotImplementedError("not yet")
        batch_scheduler.submit(self.ics_path_for(program))

    # Pack contents ------------------------------------------------------------

    def scanpack(self):
        """List the modified files (present in local directory)."""
        files = [f.strip()
                 for f in subprocess.check_output(['scanpack'], cwd=self._local).decode('utf-8').split('\n')
                 if f != '']
        return files

    def cleanpack(self):
        """Clean .o & .mod."""
        subprocess.check_call(['cleanpack', '-f'], cwd=self.abspath)

    def local2tar(self, tar_filename=None):
        """Extract the contents of the pack to a tarfile."""
        if tar_filename is None:
            tar_filename = os.path.join(self.abspath, now().stdvortex + '.tar')
        files = self.scanpack()
        with tarfile.open(tar_filename, 'w') as t:
            with self._cd_local():
                for f in files:
                    t.add(f)
        return tar_filename

    # Others -------------------------------------------------------------------

    def rmpack(self):
        """Delete pack."""
        shutil.rmtree(self.abspath)
