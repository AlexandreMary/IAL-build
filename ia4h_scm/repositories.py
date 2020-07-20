#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division
"""
Management of repositories.
"""
import subprocess
import os
import re
from contextlib import contextmanager


class GitError(Exception):
    pass


class GitProxy(object):
    
    def __init__(self, repository='.'):
        self.repository = os.path.abspath(repository)
        assert os.path.exists(os.path.join(self.repository, '.git')), \
            "There is no **repository** in here: {}".format(self.repository)
    
    @contextmanager
    def _cd_repo(self):
        """Context: in self.repository"""
        owd = os.getcwd()
        try:
            os.chdir(self.repository)
            yield self.repository
        finally:
            os.chdir(owd)
    
    def _git_cmd(self, cmd):
        """Wrapper to execute a git command."""
        return [line.strip() for line in
                subprocess.check_output(cmd, cwd=self.repository).decode('utf-8').split('\n')
                if line != '']
    
    # Repository ---------------------------------------------------------------
    
    def fetch(self, ref=None, remote=None):
        """Fetch distant **remote**."""
        print("Fetch...")
        git_cmd = ['git', 'fetch']
        if remote is not None:
            git_cmd.append(remote)
            if ref is not None:
                git_cmd.append(ref)
        self._git_cmd(git_cmd)
    
    @property
    def current_branch(self):
        """Currently checkedout branch."""
        git_cmd = ['git', 'branch']
        list_of_branches = self._git_cmd(git_cmd)
        for branch in list_of_branches:
            if branch.startswith('*'):
                branch = branch.split()[1]
                break
        return branch
    
    # Branch(es) ---------------------------------------------------------------
    
    @property
    def branches(self):
        """List of branches (local and remotes)."""
        prefix = 'branch:'
        return sorted([r[len(prefix):] for r in self.refs_get().keys()
                       if r.startswith(prefix)])
    
    @property
    def local_branches(self):
        """List of local branches."""
        return [b for b in self.branches if '/' not in b]
    
    def remote_branches(self, only_remote=''):
        """List of remote branches. All remotes if only_remote==''."""
        remote_branches = [b for b in self.branches if '/' in b]
        return [b for b in remote_branches if b.startswith(only_remote)]
    
    def checkout_new_branch(self, branch, start_ref=None):
        """Create and checkout new branch, from current ref or **start_ref**."""
        print("Checkout new branch: " + branch)
        git_cmd = ['git', 'checkout', '-b', branch]
        if start_ref is not None:
            git_cmd.append(start_ref)
        self._git_cmd(git_cmd)
    
    def pull(self, remote=None):
        """Update the local branch from remote's version."""
        git_cmd = ['git', 'pull']
        if remote is not None:
            git_cmd.append(remote)
        self._git_cmd(git_cmd)
    
    # Ref(s) -------------------------------------------------------------------
    
    def refs_get(self):
        """Get references as a dict('<type>:<ref>':<hash>), type being branch or tag."""
        git_cmd = ['git', 'show-ref']
        list_of_refs = [ref.split() for ref in self._git_cmd(git_cmd)]
        refs = {}
        for h, r in list_of_refs:
            if r.startswith('refs/tags'):
                ref = 'tag:'
            else:
                ref = 'branch:'
            ref += '/'.join(r.split('/')[2:])  # tags and branches : refs/tags/... or refs/heads/... or refs/remotes/...        
            refs[ref] = h
        return refs

    def ref_exists(self, ref):
        """Check whether a ref (tag, branch, commit) exists."""
        refs = self.refs_get()
        return (ref in (['HEAD'] +
                        [r[r.index(':') + 1:] for r in refs.keys()])  # branches & tags
                or self.commit_exists(ref))
    
    def ref_is_tag(self, ref):
        """Check whether reference is tag."""
        assert self.ref_exists(ref)
        return ref in self.tags
    
    def ref_is_branch(self, ref):
        """Check whether reference is branch."""
        assert self.ref_exists(ref)
        return ref in self.branches
    
    def refs_common_ancestor(self, ref1, ref2):
        """Common ancestor commit between 2 references (commits, branches, tags)."""
        git_cmd = ['git', 'merge-base', ref1, ref2]
        commit = self._git_cmd(git_cmd)[0]
        return commit
    
    def ref_checkout(self, ref):
        """Checkout existing reference (commit, branch, tag)."""
        print("Checkout: " + ref)
        git_cmd = ['git', 'checkout', ref]
        self._git_cmd(git_cmd)
    
    # Tag(s) -------------------------------------------------------------------
    
    @property
    def tags(self):
        """Return list of tags.""" 
        prefix = 'tag:'
        return sorted([r[len(prefix):] for r in self.refs_get().keys()
                       if r.startswith(prefix)])
    
    def tag_points_to(self, tag):
        """Return the associated commit to **tag**."""
        assert self.ref_exists(tag)
        git_cmd = ['git', 'rev-list', '-n', '1', tag]
        commit = self._git_cmd(git_cmd)[0]
        return commit
    
    def tags_between(self, start_ref, end_ref):
        """Get the list of tags between 2 references (commits, branches, tags)."""
        git_cmd = ['git', 'log', '{}...{}'.format(start_ref, end_ref),
                   '--decorate', '--simplify-by-decoration']
        _re = re.compile('commit .+ \((tag: .+)\)$')
        cmd_out = self._git_cmd(git_cmd)
        list_of_tagged_commits = [line for line in cmd_out if _re.match(line)]
        list_of_tags = [_re.match(line).group(1).split(', ') for line in list_of_tagged_commits]
        list_of_tags = [[ref[4:].strip() for ref in line if ref.startswith('tag:')]
                        for line in list_of_tags]
        return list_of_tags[::-1]
    
    # Commit(s) ----------------------------------------------------------------
    
    def commit_exists(self, commit):
        """Check whether commit is existing."""
        git_cmd = ['git', 'rev-parse', '--verify', commit + '^{commit}']
        try:
            self._git_cmd(git_cmd)
            return True
        except subprocess.CalledProcessError:
            return False
    
    # Content ------------------------------------------------------------------
    
    def touched_between(self, start_ref, end_ref):
        """
        Return the lists of Added, Modified, Deleted, Renamed (etc...) files
        between 2 references (commits, branches, tags).
        """
        assert self.ref_exists(start_ref)
        assert self.ref_exists(end_ref)
        git_cmd = ['git', 'diff', '--name-status', start_ref, end_ref]
        asdict = {'A':set(), 'R':set(), 'M':set(), 'C':set(), 'T':set(),
                  'D':set(),
                  'U':set(), 'X':set(), 'B':set()}
        touched = self._git_cmd(git_cmd)
        for line in touched:
            if line[0] in ('A', 'M', 'T', 'D'):
                asdict[line[0]].add(line.split()[1])
            elif line[0] in ('C', 'R'):
                asdict[line[0]].add(tuple(line.split()[1:3]))
            else:
                asdict[line[0]].add(line)  # FIXME: don't know how to interpret this
        for k in list(asdict.keys()):
            if len(asdict[k]) == 0:
                asdict.pop(k)
        return asdict
    
    @property
    def is_clean(self):
        """
        Tell if there are uncommited changes (working, staged) in the current
        state of the working directory.
        """
        git_cmd = ['git', 'status', '--porcelain']
        status = self._git_cmd(git_cmd)
        return len(status) == 0


class IA4H_Branch(object):
    """Utilities around IA4H branches."""
    _re_official_tags = re.compile('(?P<r>CY\d{2}((T|R)\d)?)(_(?P<b>.+)\.(?P<v>\d+))?$')
    
    def __init__(self, repository, branch_name, remote=None):
        """Hold **branch** from **repository**, possibly fetching it from **remote**."""
        self.name = branch_name
        self.repository = repository
        self.git_proxy = GitProxy(repository)
        self.git_proxy.fetch(remote=remote, ref=self.name if remote is not None else None)
        self.checkedout_branch_on_repo_before = self.git_proxy.current_branch
        if self.git_proxy.current_branch != self.name:
            assert self.git_proxy.is_clean, \
                "Working directory is not clean. Reset or commit changes manually."
            self.git_proxy.ref_checkout(self.name)
        self.git_proxy.pull(remote=remote)
    
    def __del__(self):
        if self.git_proxy.current_branch == self.name:
            if self.git_proxy.is_clean:
                self.git_proxy.ref_checkout(self.checkedout_branch_on_repo_before)
            else:
                raise Warning("Working directory is not clean at time of quiting the branch. Reset or commit changes manually.")
        else:
            raise Warning("Checkedout branch has changed and is no more {}".format(self.name))
    
    # History ------------------------------------------------------------------
    
    @property
    def official_tagged_ancestors(self):
        """All official tagged ancestors."""
        official_tags = []
        for tags in self.git_proxy.tags_between('CY38', 'HEAD'):  # CY38 is the first one under Git
            for tag in tags[::-1]:  # The latest is a priori the first one
                if self._re_official_tags.match(tag):
                    official_tags.append(tag)
        return official_tags
    
    @property
    def latest_tagged_ancestor(self):
        """Latest tagged ancestor."""
        tags = self.git_proxy.tags_between('CY38', 'HEAD')[-1]  # CY38 is the first one under Git
        return tags[0]
    
    @property
    def latest_main_release_ancestor(self):
        """Latest main release which is ancestor to the branch."""
        for tag in self.official_tagged_ancestors[::-1]:  # start from latest one
            if self._re_official_tags.match(tag).group('b') is None:  # is it a main release
                return tag
    
    @property
    def latest_official_tagged_ancestors(self):
        """Latest official tagged ancestor."""
        return self.official_tagged_ancestors[-1]
    
    @property
    def latest_official_branch_from_main_release(self):
        """
        Get information on the latest official branch between main release and
        current branch, if any.
        """
        latest_official_tagged_ancestor = self.official_tagged_ancestors[-1]
        return self._re_official_tags.match(latest_official_tagged_ancestor).groupdict()
    
    # Content ------------------------------------------------------------------
    
    def touched_files_since(self, ref):
        """Lists touched files since **ref** (commit or tag)."""
        return self.git_proxy.touched_between(ref, 'HEAD')
    
    @property
    def touched_files_since_latest_tagged_ancestor(self):
        """Lists touched files since *self.latest_tagged_ancestor*."""
        return self.git_proxy.touched_between(self.latest_tagged_ancestor, 'HEAD')
    
    @property
    def touched_files_since_latest_official_tagged_ancestor(self):
        """Lists touched files since *self.latest_official_tagged_ancestors*."""
        return self.git_proxy.touched_between(self.latest_official_tagged_ancestors, 'HEAD')
