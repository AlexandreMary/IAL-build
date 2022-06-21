#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Utility to deal with bundles in sight of their build.
"""
import six
import json
import os

from .pygmkpack import Pack, GmkpackTool
from .config import DEFAULT_BUNDLE_CACHE_DIR
from .repositories import GitProxy


class IALBundle(object):

    def __init__(self, bundle_file):
        """
        :param bundle: bundle file (yaml)
        """
        from ecbundle.bundle import Bundle
        self.bundle_file = bundle_file
        self.ecbundle = Bundle(self.bundle_file)
        self.projects = {}
        for project in self.ecbundle.get('projects'):
            for name, conf in project.items():
                self.projects[name] = dict(conf)
        self.downloaded = None  # none = unknown
        self.src_dir = DEFAULT_BUNDLE_CACHE_DIR

    def download(self,
                 cache_dir=None,
                 update=True,
                 threads=1,
                 no_colour=True,
                 dryrun=False):
        """
        Download repositories and (optionnally) checkout according versions.

        :param cache_dir: cache directory in which to download/update repositories
        :param update: if repositories are to be updated/checkedout
        :param threads: number of threads to do parallel downloads
        :param no_colour: Disable color output
        """
        import logging
        from ecbundle.logging import logger
        logger.setLevel(logging.DEBUG)
        from ecbundle import BundleDownloader
        if cache_dir is None:
            #cache_dir = self.src_dir  # FIXME: this does not work in Davai context for some reason
            cache_dir = os.getcwd()
        # downloads
        b = BundleDownloader(bundle=self.bundle_file,
                             src_dir=cache_dir,
                             update=update,
                             threads=threads,
                             no_colour=no_colour,
                             dryrun=dryrun,
                             dry_run=dryrun,
                             shallow=False,
                             forced_update=update)
        if b.download() != 0:
            raise RuntimeError("Downloading repositories failed.")
        self.downloaded = True
        self.src_dir = b.src_dir()

    def local_project_repo(self, project):
        """Path to locally downloaded repository of project."""
        assert self.src_dir is not None, "Bundle has to be downloaded or 'src_dir' attribute defined." 
        return os.path.join(self.src_dir, project)

    def tags_history(self):
        """Get tags' history for each project's version."""
        history = {}
        cwd = os.getcwd()
        for p in self.projects.keys():
            repo = GitProxy(self.local_project_repo(p))
            history[p] = []
            for t in repo.tags_history(self.projects[p]['version']):
                history[p].extend(t)
        return history

# gmkpack binding -------------------------------------------------------------

    def gmkpack_guess_pack_name(self,
                                pack_type,
                                compiler_label=None,
                                compiler_flag=None,
                                abspath=False,
                                homepack=None,
                                to_bin=False):
        """
        Guess pack name from a number of arguments.

        :param pack_type: type of pack, among ('incr', 'main')
        :param compiler_label: gmkpack compiler label
        :param compiler_flag: gmkpack compiler flag
        :param abspath: True if the absolute path to pack is requested (instead of basename)
        :param homepack: home of pack
        :param to_bin: True if the path to binaries subdirectory is requested
        """
        IAL_git_ref = self.projects['IAL']['version']
        IAL_repo_path = self.local_project_repo('IAL')  # no need to check it has been downloaded, only useful in certain cases
        packname = GmkpackTool.guess_pack_name(IAL_git_ref, compiler_label, compiler_flag,
                                               pack_type=pack_type,
                                               IAL_repo_path=IAL_repo_path)
        # finalisation
        path_elements = [packname]
        if abspath:
            path_elements.insert(0, GmkpackTool.get_homepack())
        if to_bin:
            path_elements.append('bin')
        return os.path.join(*path_elements)

    def gmkpack_create_pack(self, pack_type,
                            compiler_label=None,
                            compiler_flag=None,
                            homepack=None,
                            rootpack=None,
                            silent=False):
        """
        Create pack according to IAL version in bundle.

        :param pack_type: type of pack, among ('incr', 'main')
        :param compiler_label: Gmkpack's compiler label to be used
        :param compiler_flag: Gmkpack's compiler flag to be used
        :param homepack: directory in which to build pack
        :param rootpack: diretory in which to look for root pack (incr packs only)
        :param silent: to hide gmkpack's stdout
        """
        # prepare IAL arguments for gmkpack
        IAL_git_ref = self.projects['IAL']['version']
        assert self.downloaded, "Bundle projects to be downloaded before creation of pack."
        IAL_repo_path = self.local_project_repo('IAL')
        args = GmkpackTool.getargs(pack_type,
                                   IAL_git_ref,
                                   IAL_repo_path,
                                   compiler_label=compiler_label,
                                   compiler_flag=compiler_flag,
                                   homepack=homepack,
                                   rootpack=rootpack)
        try:
            return GmkpackTool.create_pack_from_args(args, pack_type, silent=silent)
        except Exception:
            print("Creation of pack failed !")
            raise

    def gmkpack_populate_pack(self, pack, cleanpack=False):
        """
        Populate a pack with the contents of the bundle's projects.

        :param cleanpack: if True, call cleanpack before populating
        """
        assert isinstance(pack, Pack)
        assert self.downloaded, "Bundle projects to be downloaded before populating a pack."
        try:
            pack.bundle_populate(self, cleanpack=cleanpack)
        except Exception:
            print("Failed export of bundle to pack !")
            raise
        else:
            print("\nSucessful export of bundle: {} to pack: {}".format(self.bundle_file, pack.abspath))
        finally:
            print("-" * 50)

