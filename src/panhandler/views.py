# Copyright (c) 2018, Palo Alto Networks
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# Author: Nathan Embery nembery@paloaltonetworks.com

"""
Palo Alto Networks Panhandler

panhandler is a tool to find, download, and use CCF enabled repositories

Please see http://panhandler.readthedocs.io for more information

This software is provided without support, warranty, or guarantee.
Use at your own risk.
"""
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

import yaml
from django.conf import settings
from django.contrib import messages
from django.forms import Form
from django.forms import fields
from django.forms import widgets
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.generic import RedirectView
from django.views.generic import View
from skilletlib import Panos
from skilletlib import SkilletLoader
from skilletlib.exceptions import LoginException
from skilletlib.exceptions import PanoplyException
from skilletlib.exceptions import SkilletLoaderException
from skilletlib.skillet.pan_validation import PanValidationSkillet
from skilletlib.skillet.template import TemplateSkillet
from skilletlib.snippet.panos import PanosSnippet
from yaml.scanner import ScannerError

from cnc.models import RepositoryDetails
from pan_cnc.lib import cnc_utils
from pan_cnc.lib import db_utils
from pan_cnc.lib import git_utils
from pan_cnc.lib import snippet_utils
from pan_cnc.lib import task_utils
from pan_cnc.lib.exceptions import ImportRepositoryException
from pan_cnc.lib.exceptions import RepositoryPermissionsException
from pan_cnc.lib.exceptions import SnippetRequiredException
from pan_cnc.lib.validators import FqdnOrIp
from pan_cnc.views import CNCBaseAuth
from pan_cnc.views import CNCBaseFormView
from pan_cnc.views import CNCView
from pan_cnc.views import EditTargetView
from pan_cnc.views import ProvisionSnippetView
from panhandler.lib import app_utils
from .models import Collection
from .models import Favorite


class WelcomeView(CNCView):
    template_name = "panhandler/welcome.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        up_to_date = app_utils.is_up_to_date()
        if up_to_date is None:
            update_required = "error"
        elif up_to_date:
            update_required = "false"
        else:
            print('Panhandler needs an update!')
            update_required = "true"

        context['update_required'] = update_required

        db_utils.initialize_default_repositories('panhandler')

        self.request.session['app_dir'] = 'panhandler'

        return context


class PanhandlerAppFormView(CNCBaseFormView):

    def get_snippet(self):
        return self.snippet

    def load_skillet_by_name(self, skillet_name) -> (dict, None):
        """
        Loads application specific skillet
        :param skillet_name:
        :return:
        """

        application_skillets_dir = Path(os.path.join(settings.SRC_PATH, self.app_dir, 'snippets'))
        skillet_loader = SkilletLoader()
        app_skillets = skillet_loader.load_all_skillets_from_dir(application_skillets_dir)
        for skillet in app_skillets:
            if skillet.name == skillet_name:
                return skillet.skillet_dict

        return None


class ImportRepoView(PanhandlerAppFormView):
    # define initial dynamic form from this snippet metadata
    snippet = 'import_repo'
    next_url = '/provision'
    template_name = 'panhandler/import_repo.html'
    app_dir = 'panhandler'

    def get_context_data(self, **kwargs):
        recommended_links = app_utils.get_recommended_links()
        context = super().get_context_data(**kwargs)
        context['links'] = recommended_links
        return context

    # once the form has been submitted and we have all the values placed in the workflow, execute this
    def form_valid(self, form):
        workflow = self.get_workflow()

        # get the values from the user submitted form here
        url = workflow.get('url')
        repo_name = workflow.get('repo_name')

        if not re.match(r'^[a-zA-Z0-9-_ \.]*$', repo_name):
            print('Repository name is invalid!')
            messages.add_message(self.request, messages.ERROR, 'Invalid Repository Name')
            return HttpResponseRedirect('repos')

        user_dir = os.path.expanduser('~/.pan_cnc')
        snippets_dir = os.path.join(user_dir, 'panhandler/repositories')
        repo_dir = os.path.join(snippets_dir, repo_name)

        if os.path.exists(repo_dir):
            if os.path.isdir(repo_dir) and len(os.listdir(repo_dir)) == 0:
                print('Reusing existing repository directory')
            else:
                messages.add_message(self.request, messages.ERROR, 'A Repository with this name already exists')
                return HttpResponseRedirect('repos')
        else:
            try:
                os.makedirs(repo_dir, mode=0o700)

            except PermissionError:
                messages.add_message(self.request, messages.ERROR,
                                     'Could not create repository directory, Permission Denied')
                return HttpResponseRedirect('repos')
            except OSError:
                messages.add_message(self.request, messages.ERROR,
                                     'Could not create repository directory')
                return HttpResponseRedirect('repos')

        # where to clone from
        clone_url = url.strip()

        # if this is an SSH based url, ensure the host key is known
        if clone_url.startswith('git@') or clone_url.startswith('ssh'):
            is_known, message = git_utils.ensure_known_host(clone_url)
            if not is_known:
                messages.add_message(self.request, messages.ERROR,
                                     f'Could not verify SSH Host Key! {message}')

                return HttpResponseRedirect('/ssh_key')
            else:
                messages.add_message(self.request, messages.INFO, 'Added the following SSH Host key to known_hosts: '
                                                                  f'{message}')

        if 'github' in url.lower():
            details = git_utils.get_repo_upstream_details(repo_name, url, self.app_dir)
            if 'clone_url' in details:
                clone_url = details['clone_url']

        try:
            message = git_utils.clone_repository(repo_dir, repo_name, clone_url)
            print(message)
        except RepositoryPermissionsException:
            messages.add_message(self.request, messages.ERROR,
                                 'SSH Permissions Error. Please add your SSH Public key to the upstream repository')

            return HttpResponseRedirect('/ssh_key')

        except ImportRepositoryException as ire:
            messages.add_message(self.request, messages.ERROR, f'Could not Import Repository: {ire}')

        else:
            repos = cnc_utils.get_long_term_cached_value(self.app_dir, 'imported_repositories')

            # FIX for #148
            if repos is None:
                repos = list()

            try:
                repo_detail = git_utils.get_repo_details(repo_name, repo_dir, self.app_dir)
            except RepositoryPermissionsException:
                messages.add_message(self.request, messages.ERROR,
                                     'SSH Permissions Error. Please add the Deploy key to the upstream repository')
                return HttpResponseRedirect('/ssh_key')

            repos.append(repo_detail)
            cnc_utils.set_long_term_cached_value(self.app_dir, 'imported_repositories', repos, 604800,
                                                 'imported_git_repos')

            db_utils.initialize_repo(repo_detail)

            debug_errors = snippet_utils.debug_snippets_in_repo(Path(repo_dir), list())

            loaded_skillets = db_utils.load_skillets_from_repo(repo_name)

            # check each snippet found for dependencies
            for skillet in loaded_skillets:
                for depends in skillet['depends']:
                    url = depends.get('url', None)
                    branch = depends.get('branch', 'master')

                    # now check each repo to see if we already have it, add an error if not
                    found = False

                    for repo in repos:
                        if repo['url'] == url and repo['branch'] == branch:
                            found = True
                            break

                    if not found:
                        messages.add_message(self.request, messages.ERROR,
                                             f'Unresolved Dependency found!! Please ensure you import the following'
                                             f'repository: {url} with branch: {branch}')

            if debug_errors:
                messages.add_message(self.request, messages.ERROR,
                                     'Found Skillets with errors! Please open an issue on '
                                     'this repository to help resolve this issue')

                for d in debug_errors:
                    if 'err_list' in d and 'path' in d and 'severity' in d:

                        for e in d['err_list']:

                            if d['severity'] == 'warn':
                                level = messages.WARNING

                            else:
                                level = messages.ERROR

                            messages.add_message(self.request, level, f'Skillet: {d["path"]}\n\nError: {e}')
            else:
                messages.add_message(self.request, messages.INFO, 'Imported Repository Successfully')

        # fix for gl #3 - be smarter about clearing the cache
        db_utils.update_skillet_cache()
        # snippet_utils.invalidate_snippet_caches(self.app_dir)

        # git_utils.update_repo_in_cache(repo_name, repo_dir, repo_detail)
        return HttpResponseRedirect('repos')


class ListReposView(CNCView):
    template_name = 'panhandler/repos.html'
    app_dir = 'panhandler'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        snippets_dir = Path(os.path.join(os.path.expanduser('~/.pan_cnc'), 'panhandler', 'repositories'))

        try:
            if not snippets_dir.exists():
                messages.add_message(self.request, messages.ERROR,
                                     'Could not load repositories from directory as it does not exists')
                context['repos'] = list()
                return context

        except PermissionError as pe:
            print(pe)
            context['repos'] = list()
            return context

        except OSError as oe:
            print(oe)
            context['repos'] = list()
            return context

        repos = cnc_utils.get_long_term_cached_value(self.app_dir, 'imported_repositories')

        if repos is not None:
            print('Returning cached repos')
            context['repos'] = repos

        else:
            repos = list()

            for d in snippets_dir.iterdir():
                git_dir = d.joinpath('.git')

                if git_dir.exists() and git_dir.is_dir():
                    repo_detail = db_utils.get_repository_details(d.name)
                    if not repo_detail:
                        repo_detail = git_utils.get_repo_details(d.name, d, self.app_dir)
                        db_utils.initialize_repo(repo_detail)
                    repos.append(repo_detail)
                    db_utils.initialize_repo(repo_detail)
                    continue

            # cache the repos list for 1 week. this will be cleared when we import a new repository or otherwise
            # change the repo list somehow
            cnc_utils.set_long_term_cached_value(self.app_dir, 'imported_repositories', repos, 604800,
                                                 'imported_git_repos')
            context['repos'] = repos

        return context


class RepoDetailsView(CNCView):
    template_name = 'panhandler/repo_detail.html'
    app_dir = 'panhandler'

    @staticmethod
    def __get_repo_dir(repo_name: str):
        user_dir = os.path.expanduser('~')
        return os.path.join(user_dir, '.pan_cnc', 'panhandler', 'repositories', repo_name)

    def get(self, request, *args, **kwargs):
        repo_name = self.kwargs['repo_name']
        repo_detail = dict()
        repo_detail['name'] = repo_name
        repo_dir = self.__get_repo_dir(repo_name)
        if not os.path.exists(repo_dir) or not RepositoryDetails.objects.filter(name=repo_name).exists():
            messages.add_message(self.request, messages.ERROR, 'Repository does not exist!')
            return HttpResponseRedirect('/panhandler/repos')

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        # always ensure workflow related items are removed from session when we get here in case a user
        # cancels their workflow in the middle of it without it completing properly
        self.clean_up_workflow()

        repo_name = self.kwargs['repo_name']
        # retrieve details from the db where possible
        repo_detail = db_utils.get_repository_details(repo_name)
        repo_dir = self.__get_repo_dir(repo_name)

        if not repo_detail:
            # no db record exists or json is not parsable
            repo_detail = git_utils.get_repo_details(repo_name, repo_dir, self.app_dir)

        # initialize will set up db object only if needed
        skillets_from_repo = db_utils.initialize_repo(repo_detail)

        if 'error' in repo_detail:
            messages.add_message(self.request, messages.ERROR, repo_detail['error'])

        # get a list of all collections found in this repo
        collections = list()
        for skillet in skillets_from_repo:
            if 'labels' in skillet and 'collection' in skillet['labels']:
                collection = skillet['labels']['collection']

                if type(collection) is str:
                    if collection not in collections:
                        collections.append(collection)

                elif type(collection) is list:
                    for collection_member in collection:
                        if collection_member not in collections:
                            collections.append(collection_member)

        repo_record = RepositoryDetails.objects.get(name=repo_name)

        status = git_utils.get_git_status(repo_dir)
        if 'branch is ahead' in status:
            needs_push = True
        else:
            needs_push = False

        context = super().get_context_data(**kwargs)
        context['repo_detail'] = repo_detail
        context['repo_name'] = repo_name
        context['status'] = status
        context['needs_push'] = needs_push
        context['repo_record'] = repo_record
        context['snippets'] = skillets_from_repo
        context['collections'] = collections
        return context


class UpdateRepoView(CNCBaseAuth, RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        repo_name = kwargs['repo_name']
        branch = kwargs['branch']
        user_dir = os.path.expanduser('~')
        repo_dir = os.path.join(user_dir, '.pan_cnc', 'panhandler', 'repositories', repo_name)

        if not os.path.exists(repo_dir):
            messages.add_message(self.request, messages.ERROR, 'Repository directory does not exist!')
            return f'/panhandler/repo_detail/{repo_name}'

        # always clear the repo detail cache to pull new branches and commits
        cnc_utils.set_long_term_cached_value(self.app_dir, f'{repo_name}_detail', None, 0, 'git_repo_details')

        msg = git_utils.update_repo(repo_dir, branch)

        repo_detail = git_utils.get_repo_details(repo_name, repo_dir, self.app_dir)
        repo_detail_json = json.dumps(repo_detail)

        (repository_object, needs_index) = RepositoryDetails.objects.get_or_create(
            name=repo_name,
            defaults={'url': repo_detail.get('url'),
                      'details_json': repo_detail_json
                      }
        )

        level = messages.INFO

        if 'Error' in msg:
            level = messages.ERROR
            cnc_utils.evict_cache_items_of_type(self.app_dir, 'imported_git_repos')

        elif 'updated' in msg or 'Checked out new' in msg:
            # msg updated will catch both switching branches as well as new commits
            level = messages.INFO

            # remove all python3 init touch files if there is an update
            task_utils.python3_reset_init(repo_dir)

            # set needs_index flag regardless of creation status
            needs_index = True

        else:
            print(f'update repo msg was: {msg}')

        messages.add_message(self.request, level, msg)

        # check if there are new branches available
        repo_branches = git_utils.get_repo_branches_from_dir(repo_dir)
        if repo_detail['branches'] != repo_branches:
            messages.add_message(self.request, messages.INFO, 'New Branches are available')

        # check each snippet found for dependencies
        repos = cnc_utils.get_long_term_cached_value(self.app_dir, 'imported_repositories')

        if needs_index:
            loaded_skillets = db_utils.refresh_skillets_from_repo(repo_name)
        else:
            loaded_skillets = db_utils.load_skillets_from_repo(repo_name)

        for skillet in loaded_skillets:
            for depends in skillet['depends']:
                url = depends.get('url', None)
                branch = depends.get('branch', 'master')

                # now check each repo to see if we already have it, add an error if not
                found = False

                for repo in repos:
                    if repo['url'] == url and repo['branch'] == branch:
                        found = True
                        break

                if not found:
                    messages.add_message(self.request, messages.ERROR,
                                         f'Unresolved Dependency found!! Please ensure you import the following'
                                         f' repository: {url} with branch: {branch}')

        debug_errors = snippet_utils.debug_snippets_in_repo(Path(repo_dir), list())

        if debug_errors:
            messages.add_message(self.request, messages.ERROR, 'Found Skillets with errors! Please open an issue on '
                                                               'this repository to help resolve this issue')
            for d in debug_errors:
                if 'err_list' in d and 'path' in d:
                    for e in d['err_list']:
                        if d['severity'] == 'warn':
                            level = messages.WARNING

                        else:
                            level = messages.ERROR

                        messages.add_message(self.request, level, f'Skillet: {d["path"]}\n\nError: {e}')

        # Remove temp files as part of fix for #187
        path = Path(repo_dir)
        touch_files = path.rglob('.cnc_tmp_*')
        for tf in touch_files:
            print(f'Removing temp file: {tf}')
            tf.unlink()

        repository_object.details_json = json.dumps(repo_detail)
        repository_object.save()

        # manage cached items as well
        git_utils.update_repo_detail_in_cache(repo_detail, self.app_dir)
        # fix for gl #3 - be smarter about clearing the cache
        db_utils.update_skillet_cache()
        # snippet_utils.invalidate_snippet_caches(self.app_dir)

        return f'/panhandler/repo_detail/{repo_name}'


class UpdateAllReposView(CNCBaseAuth, RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        user_dir = os.path.expanduser('~')
        base_dir = os.path.join(user_dir, '.pan_cnc', 'panhandler', 'repositories')
        base_path = Path(base_dir)

        try:
            base_path.stat()

        except PermissionError:
            messages.add_message(self.request, messages.ERROR,
                                 'Could not update, Permission Denied')
            return '/panhandler/repos'

        except OSError:
            messages.add_message(self.request, messages.ERROR,
                                 'Could not update, Access Error for repository directory')
            return '/panhandler/repos'

        if not base_path.exists():
            messages.add_message(self.request, messages.ERROR,
                                 'Could not update, repositories directory does not exist')
            return '/panhandler/repos'

        err_condition = False
        updates = list()

        for d in base_path.iterdir():
            git_dir = d.joinpath('.git')

            if git_dir.exists() and git_dir.is_dir():
                msg = git_utils.update_repo(str(d))

                if 'Error' in msg:
                    print(f'Error updating Repository: {d.name}')
                    print(msg)
                    messages.add_message(self.request, messages.ERROR, f'Could not update repository {d.name}')
                    err_condition = True

                elif 'updated' in msg or 'Checked out new' in msg:
                    print(f'Updated Repository: {d.name}')
                    updates.append(d.name)
                    cnc_utils.set_long_term_cached_value(self.app_dir, f'{d.name}_detail', None, 0, 'git_repo_details')

                    # remove all python3 init touch files if there is an update
                    task_utils.python3_reset_init(str(d))

                    # Remove temp files as part of fix for #187
                    touch_files = d.rglob('.cnc_tmp_*')
                    for tf in touch_files:
                        print(f'Removing temp file: {tf}')
                        tf.unlink()

                    # re-index skillets in this dir
                    db_utils.refresh_skillets_from_repo(str(d))

        if not err_condition:
            repos = ", ".join(updates)
            messages.add_message(self.request, messages.SUCCESS, f'Successfully Updated repositories: {repos}')

        # fix for gl #3 - be smarter about clearing the cache
        db_utils.update_skillet_cache()
        # snippet_utils.invalidate_snippet_caches(self.app_dir)
        cnc_utils.evict_cache_items_of_type(self.app_dir, 'imported_git_repos')
        return '/panhandler/repos'


class RemoveRepoView(CNCBaseAuth, RedirectView):
    app_dir = 'panhandler'

    def get_redirect_url(self, *args, **kwargs):
        repo_name = kwargs['repo_name']
        # we are going to keep the snippets in the snippets dir in the panhandler app
        # get the dir where all apps are installed
        # src_dir = settings.SRC_PATH
        # # get the panhandler app dir
        # panhandler_dir = os.path.join(src_dir, 'panhandler')
        # # get the snippets dir under that
        # snippets_dir = os.path.join(panhandler_dir, 'snippets')
        # repo_dir = os.path.abspath(os.path.join(snippets_dir, repo_name))

        user_dir = os.path.expanduser('~')
        snippets_dir = os.path.join(user_dir, '.pan_cnc', 'panhandler', 'repositories')
        repo_dir = os.path.join(snippets_dir, repo_name)

        if snippets_dir in repo_dir:
            print(f'Removing repo {repo_name}')
            if os.path.exists(repo_dir):
                shutil.rmtree(repo_dir, ignore_errors=True)
            else:
                print(f'dir {repo_dir} is already gone!')

            cnc_utils.set_long_term_cached_value(self.app_dir, f'{repo_name}_detail', None, 0, 'snippet')
            # Fix for #197 - ensure we delete old repo details
            cache_repo_name = repo_name.replace(' ', '_')
            cnc_utils.set_long_term_cached_value(self.app_dir, f'git_utils_upstream_{cache_repo_name}', None, 0,
                                                 'git_repo_details')
            cnc_utils.evict_cache_items_of_type(self.app_dir, 'imported_git_repos')

        repository_object = RepositoryDetails.objects.get(name=repo_name)
        repository_object.delete()

        # no need for this per gl #3
        # snippet_utils.invalidate_snippet_caches(self.app_dir)

        # fix for #207 - no need to invalid the snippet cache when we have all the skillets in the db
        # all_skillets = app_utils.load_all_skillets()
        # cnc_utils.set_long_term_cached_value(self.app_dir, 'all_snippets', all_skillets, -1)

        # this is now moved into it's own library function per gitlab issue #3
        db_utils.update_skillet_cache()

        messages.add_message(self.request, messages.SUCCESS, 'Repo Successfully Removed')
        return '/panhandler/repos'


class CreateSkilletView(PanhandlerAppFormView):
    snippet = 'create_skillet'
    app_dir = 'panhandler'
    title = "Skillet Generator"
    header = "Create a New Skillet"

    def get_context_data(self, **kwargs):
        repo_name = self.kwargs.get('repo_name', None)
        self.request.session['create_skillet_repo_name'] = repo_name
        return super().get_context_data(**kwargs)

    # once the form has been submitted and we have all the values placed in the workflow, execute this
    def form_valid(self, form):
        try:
            repo_name = self.request.session.pop('create_skillet_repo_name')
        except KeyError:
            messages.add_message(self.request, messages.ERROR, 'Could not edit Skillet, malformed environment')
            return HttpResponseRedirect('/panhandler/repos')

        workflow = self.get_workflow()
        local_branch = workflow.get('local_branch_name', None)
        commit_message = workflow.get('commit_message', None)
        skillet_name = workflow.get('skillet_name', None)
        skillet_label = workflow.get('skillet_label', None)
        skillet_type = workflow.get('skillet_type', None)
        skillet_description = workflow.get('skillet_description', None)

        # let's cheat and grab a snippets list from the context - Skillet Builder tools can populate this for us
        skillet_snippets = workflow.get('snippets', list())

        collection_name = workflow.get('collection_name', 'Unknown')

        new_skillet = dict()
        new_skillet['name'] = skillet_name
        new_skillet['label'] = skillet_label
        new_skillet['description'] = skillet_description
        new_skillet['type'] = skillet_type

        new_skillet['labels'] = {
            'collection': collection_name
        }

        new_skillet['variables'] = list()
        new_skillet['snippets'] = skillet_snippets

        user_dir = os.path.expanduser('~/.pan_cnc')
        snippets_dir = os.path.join(user_dir, 'panhandler/repositories')
        repo_dir = os.path.join(snippets_dir, repo_name)

        skillet_path = os.path.join(repo_dir, skillet_name)

        # ensure we can create the appropriate directory
        if os.path.exists(skillet_path):
            messages.add_message(self.request, messages.ERROR,
                                 'Could not Create Skillet, Directory already exists in repo')
            return HttpResponseRedirect(f'/panhandler/repo_detail/{repo_name}')

        try:
            os.makedirs(skillet_path)
        except OSError:
            messages.add_message(self.request, messages.ERROR,
                                 'Could not Create Skillet, Could not create directory!')
            return HttpResponseRedirect(f'/panhandler/repo_detail/{repo_name}')

        # check to ensure no skillet exists in the repo root, this will prevent snippet_utils from indexing any
        # child directories and this skillet will never been seen!
        if os.path.exists(os.path.join(repo_dir, '.meta-cnc.yaml')):
            messages.add_message(self.request, messages.ERROR,
                                 'Could not Create Skillet, Found a Skillet file in the Repository Root!')
            return HttpResponseRedirect(f'/panhandler/repo_detail/{repo_name}')

        # ensure this skillet name does not already exist
        existing_skillet = db_utils.load_skillet_by_name(skillet_name)

        if existing_skillet:
            messages.add_message(self.request, messages.ERROR,
                                 'Could not create Skillet, Skillet with that name already exists')
            return HttpResponseRedirect(f'/panhandler/repo_detail/{repo_name}')

        try:
            skillet_content = yaml.safe_dump(new_skillet)

        except (ScannerError, ValueError):
            messages.add_message(self.request, messages.ERROR,
                                 'Syntax Error! Refusing to overwrite Skillet metadata file.')
            return HttpResponseRedirect(f'/panhandler/repo_detail/{repo_name}')

        git_utils.checkout_local_branch(repo_dir, local_branch)

        skillet_file_path = os.path.join(skillet_path, '.meta-cnc.yaml')

        with open(skillet_file_path, 'w') as skillet_file:
            skillet_file.write(skillet_content)

        git_utils.commit_local_changes(repo_dir, commit_message, skillet_file_path)

        messages.add_message(self.request, messages.SUCCESS, 'Skillet Created!')

        # go ahead and refresh all the found skillet
        db_utils.refresh_skillets_from_repo(repo_name)

        cnc_utils.set_long_term_cached_value(self.app_dir, f'{repo_name}_detail', None, 0, 'snippet')
        return HttpResponseRedirect(f'/panhandler/edit_skillet/{repo_name}/{skillet_name}')


class UpdateSkilletView(PanhandlerAppFormView):
    snippet = 'edit_skillet'
    next_url = '/provision'
    app_dir = 'panhandler'
    template_name = 'panhandler/edit_skillet.html'

    def get_header(self) -> str:
        """
        override default get_header method on CNCBaseAuth

        :return: str containing name of the skillet we are editting
        """
        if self.service:
            return self.service.get('label', 'Edit Skillet')

        return 'Edit Skillet'

    def get_context_data(self, **kwargs):
        skillet_name = self.kwargs.get('skillet', None)
        repo_name = self.kwargs.get('repo_name', None)

        # get skillet metadata
        skillet_dict = db_utils.load_skillet_by_name(skillet_name)

        # get the contents of the meta-cnc.yaml file as a str
        skillet_contents = snippet_utils.read_skillet_metadata(skillet_dict)

        skillet_loader = SkilletLoader()
        skillet = skillet_loader.create_skillet(skillet_dict=skillet_dict)

        # call get_snippets to ensure we load 'file' attributes into 'element'
        skillet.get_snippets()

        skillet_json = json.dumps(skillet_dict)

        if skillet is None:
            raise SnippetRequiredException('Could not find skillet to edit')

        skillet_path = skillet_dict.get('snippet_path')

        # save these values to the user session for later use on form_submit
        self.request.session['edit_skillet_repo_name'] = repo_name
        self.request.session['edit_skillet_skillet_path'] = skillet_path

        self.prepopulated_form_values['skillet_contents'] = skillet_contents

        context = super().get_context_data(**kwargs)
        context['skillet_contents'] = skillet_contents
        context['skillet_json'] = skillet_json
        context['skillet'] = skillet
        context['title'] = 'Edit Skillet Metadata'
        context['header'] = 'Panhandler Skillet'
        return context

    def form_valid(self, form):

        try:
            skillet_path = self.request.session['edit_skillet_skillet_path']
            repo_name = self.request.session['edit_skillet_repo_name']
        except KeyError:
            messages.add_message(self.request, messages.ERROR, 'Could not edit Skillet, malformed environment')
            return HttpResponseRedirect('/panhandler/repos')

        workflow = self.get_workflow()
        local_branch = workflow.get('local_branch_name', None)
        skillet_json = workflow.get('skillet_contents', {})
        commit_message = workflow.get('commit_message', None)

        try:
            skillet_dict = json.loads(skillet_json)
            skillet_content = yaml.safe_dump(skillet_dict)

        except (ScannerError, ValueError):
            messages.add_message(self.request, messages.ERROR,
                                 'Syntax Error! Refusing to overwrite Skillet metadata file.')
            return HttpResponseRedirect(f'/panhandler/repo_detail/{repo_name}')

        skillet_loader = SkilletLoader()
        debug_errors = skillet_loader.debug_skillet_structure(skillet_dict)

        # debug skillet structure
        for d in debug_errors:
            messages.add_message(self.request, messages.ERROR, f'Skillet Error: {d}')

        skillet = skillet_loader.create_skillet(skillet_dict=skillet_dict)

        # FIXME - this has been reworked in skilletlib for all skillet types
        # FIXME - possibly need to ensure declared variables that are also outputs are not flagged here
        if 'pan' in skillet.type:
            # extra check to ensure all variables are defined
            for snippet in skillet.get_snippets():
                cmd = snippet.metadata.get('cmd', 'set')
                if cmd == 'set':
                    snippet_vars = list(snippet.get_variables_from_template(snippet.metadata.get('xpath', '')))
                    snippet_vars.extend(list(snippet.get_variables_from_template(snippet.metadata.get('element', ''))))
                    for var in snippet_vars:
                        found = False
                        for declared_var in skillet.variables:
                            if var == declared_var['name']:
                                found = True
                                break

                        if not found:
                            messages.add_message(self.request, messages.WARNING, f'Found undeclared variable: {var} '
                                                                                 f'in {skillet.label}: {snippet.name}')

        user_dir = os.path.expanduser('~')
        snippets_dir = os.path.join(user_dir, '.pan_cnc', 'panhandler', 'repositories')
        repo_dir = os.path.join(snippets_dir, repo_name)

        git_utils.checkout_local_branch(repo_dir, local_branch)

        skillet_file_path = os.path.join(skillet_path, '.meta-cnc.yaml')

        with open(skillet_file_path, 'w') as skillet_file:
            skillet_file.write(skillet_content)

        git_utils.commit_local_changes(repo_dir, commit_message, skillet_file_path)

        messages.add_message(self.request, messages.SUCCESS, 'Skillet updated!')

        db_utils.refresh_skillets_from_repo(repo_name)

        cnc_utils.set_long_term_cached_value(self.app_dir, f'{repo_name}_detail', None, 0, 'snippet')
        return HttpResponseRedirect(f'/panhandler/repo_detail/{repo_name}')


class ListSkilletCollectionsView(CNCView):
    template_name = 'panhandler/collections.html'
    app_dir = 'panhandler'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cached_collections = cnc_utils.get_long_term_cached_value(self.app_dir, 'cached_collections')
        cached_collections_info = cnc_utils.get_long_term_cached_value(self.app_dir, 'cached_collections_info')
        if cached_collections is not None:
            context['collections'] = cached_collections
            context['collections_info'] = cached_collections_info
            return context

        # return a list of all defined collections
        collections = db_utils.load_all_skillet_label_values('collection')

        # build dict of collections related to other collections (if any)
        # and a count of how many skillets are in the collection
        collections_info = dict()

        # manually create a collection called 'All'
        all_skillets = 'All Skillets'

        # get the full list of all snippets
        all_snippets = db_utils.load_all_skillets()

        collections_info[all_skillets] = dict()
        collections_info[all_skillets]['count'] = len(all_snippets)
        collections_info[all_skillets]['related'] = list()

        # iterate over the list of collections
        for c in collections:
            if c not in collections_info:
                collections_info[c] = dict()
                collections_info[c]['count'] = 0

            skillets = db_utils.load_skillets_with_label('collection', c)
            collections_info[c]['count'] = len(skillets)
            related = list()

            for skillet in skillets:
                if 'labels' in skillet and 'collection' in skillet['labels']:
                    if type(skillet['labels']['collection']) is list:
                        for related_collection in skillet['labels']['collection']:
                            if related_collection != c and related_collection not in related:
                                related.append(related_collection)

            collections_info[c]['related'] = json.dumps(related)

        collections.append('Kitchen Sink')
        collections.append(all_skillets)
        context['collections'] = collections
        context['collections_info'] = collections_info

        cnc_utils.set_long_term_cached_value(self.app_dir, 'cached_collections',
                                             collections, 86400, 'snippet')
        cnc_utils.set_long_term_cached_value(self.app_dir, 'cached_collections_info',
                                             collections_info, 86400, 'snippet')
        return context


class ListSkilletsInCollectionView(CNCView):
    template_name = 'panhandler/collection.html'
    app_dir = 'panhandler'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        collection = self.kwargs.get('collection', 'Kitchen Sink')
        print(f'Getting all snippets with collection label {collection}')

        if collection == 'All Skillets':
            all_skillets = db_utils.load_all_skillets()

            # remove app type skillets from this list for #196
            skillets = list(s for s in all_skillets if s['type'] != 'app')
        else:
            skillets = db_utils.load_skillets_with_label('collection', collection)

        # Check if the skillet builder has specified an order for their Skillets
        # if so, sort them that way be default, otherwise sort by name
        order_index = 1000
        default_sort = 'name'
        for skillet in skillets:
            if 'order' not in skillet['labels']:
                skillet['labels']['order'] = order_index
                order_index += 1
            else:
                default_sort = 'order'

        context['skillets'] = skillets
        context['collection'] = collection
        context['default_sort'] = default_sort

        return context


class ViewSkilletView(ProvisionSnippetView):

    def get_snippet(self):
        """
        Override the get_snippet as the snippet_name is passed as a kwargs param and not a POST or in the session
        :return: name of the skillet found in the kwargs
        """
        skillet = self.kwargs.get('skillet', '')
        if skillet is not None or skillet != '':
            self.snippet = skillet
            self.save_value_to_workflow('snippet_name', skillet)
        return skillet

    def load_skillet_by_name(self, skillet_name) -> (dict, None):
        return db_utils.load_skillet_by_name(skillet_name)


class CheckAppUpdateView(CNCBaseAuth, RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        cnc_utils.evict_cache_items_of_type('panhandler', 'app_update')
        return '/'


# Validation Testing Class below
class ExecuteValidationSkilletView(ProvisionSnippetView):
    header = 'Configure Validation Skillet'

    def generate_dynamic_form(self, data=None) -> Form:
        dynamic_form = super().generate_dynamic_form(data)
        choices_list = [('offline', 'Offline'), ('online', 'Online')]
        description = 'Validation Mode'
        mode = self.get_value_from_workflow('mode', 'online')
        default = mode
        required = True
        help_text = 'Online mode will pull configuration directly from an accessible PAN-OS device. Offline ' \
                    'allows an XML configuration file to be uploaded.'
        dynamic_form.fields['mode'] = fields.ChoiceField(choices=choices_list,
                                                         label=description, initial=default,
                                                         required=required, help_text=help_text)

        # Uncomment when skilletlib can take a config_source
        # choices_list = list()
        # candidate = ('candidate', 'Candidate')
        # running = ('running', 'Running')
        # choices_list.append(candidate)
        # choices_list.append(running)
        # dynamic_form.fields['config_source'] = forms.ChoiceField(widget=forms.Select, choices=tuple(choices_list),
        #                                                          label='Configuration Source',
        #                                                          initial='running', required=True,
        #                                                          help_text='Which configuration file to use '
        #                                                                    'for validation')
        #
        # f = dynamic_form.fields['config_source']
        # w = f.widget
        # w.attrs.update({'data-source': 'mode'})
        # w.attrs.update({'data-value': 'online'})
        #
        return dynamic_form

    def get_snippet(self):
        """
        Override the get_snippet as the snippet_name is passed as a kwargs param and not a POST or in the session
        :return: name of the skillet found in the kwargs
        """
        skillet = self.kwargs.get('skillet', '')
        self.save_value_to_workflow('snippet_name', skillet)
        self.snippet = skillet
        return skillet

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        if self.service is not None:

            if 'type' not in self.service:
                return super().get_context_data(**kwargs)

            self.header = 'Perform Validation'
            self.title = self.service['label']
            context['header'] = 'Perform Validation'
            context['title'] = self.service['label']

        return context

    def form_valid(self, form):
        self.request.session['next_url'] = self.next_url
        mode = self.request.POST.get('mode', 'online')
        # config_source = self.request.POST.get('config_source', 'running')
        self.save_value_to_workflow('mode', mode)
        # self.save_value_to_workflow('config_source', config_source)
        return HttpResponseRedirect('/panhandler/validate-results')


class ViewValidationResultsView(EditTargetView):
    header = 'Perform Validation - Step 2'
    title = 'Validation - Step 2'
    template_name = 'pan_cnc/dynamic_form.html'

    def get_header(self) -> str:
        workflow_name = self.request.session.get('workflow_name', None)
        next_step = self.request.session.get('workflow_ui_step', None)

        header = self.header
        if workflow_name is not None:
            workflow_skillet_dict = db_utils.load_skillet_by_name(workflow_name)
            if workflow_skillet_dict is not None:
                header = workflow_skillet_dict.get('label', self.header)

        if next_step is None:
            return header
        else:
            return f"Step {next_step}: {header}"

    def get(self, request, *args, **kwargs) -> Any:
        """
        """
        mode = self.get_value_from_workflow('mode', 'online')
        workflow_name = self.request.session.get('workflow_name', False)

        if mode == 'online' and workflow_name:

            if {'TARGET_IP', 'TARGET_USERNAME', 'TARGET_PASSWORD'}.issubset(self.get_workflow().keys()):
                print('Skipping validation input as we already have this information cached')
                snippet = self.get_value_from_workflow('snippet_name', None)
                self.meta = db_utils.load_skillet_by_name(snippet)

                target_ip = self.get_value_from_workflow('TARGET_IP', '')
                # target_port = self.get_value_from_workflow('TARGET_PORT', 443)
                target_username = self.get_value_from_workflow('TARGET_USERNAME', '')
                target_password = self.get_value_from_workflow('TARGET_PASSWORD', '')
                data = {'TARGET_IP': target_ip, 'TARGET_USERNAME': target_username, 'TARGET_PASSWORD': target_password}
                form = self.generate_dynamic_form(data=data)

                # this is part of a workflow, and we already have this information in the context
                return self.form_valid(form)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['header'] = self.header
        return context

    def generate_dynamic_form(self, data=None) -> Form:

        form = Form(data=data)

        meta = self.meta
        if meta is None:
            raise SnippetRequiredException('Could not find a valid skillet!!')

        mode = self.get_value_from_workflow('mode', 'online')

        if mode == 'online':
            self.title = 'PAN-OS NGFW to Validate'
            self.help_text = 'This form allows you to enter the connection information for a PAN-OS NGFW. This' \
                             'tool will connect to that device and pull it\'s configuration to perform the' \
                             'validation.'

            target_ip_label = 'Target IP'
            target_username_label = 'Target Username'
            target_password_label = 'Target Password'

            target_ip = self.get_value_from_workflow('TARGET_IP', '')
            # target_port = self.get_value_from_workflow('TARGET_PORT', 443)
            target_username = self.get_value_from_workflow('TARGET_USERNAME', '')
            target_password = self.get_value_from_workflow('TARGET_PASSWORD', '')

            target_ip_field = fields.CharField(label=target_ip_label, initial=target_ip, required=True,
                                               validators=[FqdnOrIp])
            target_username_field = fields.CharField(label=target_username_label, initial=target_username,
                                                     required=True)
            target_password_field = fields.CharField(widget=widgets.PasswordInput(render_value=True), required=True,
                                                     label=target_password_label,
                                                     initial=target_password)

            form.fields['TARGET_IP'] = target_ip_field
            form.fields['TARGET_USERNAME'] = target_username_field
            form.fields['TARGET_PASSWORD'] = target_password_field
        else:
            self.title = 'PAN-OS XML Configuration to Validate'
            self.help_text = 'This form allows you to paste in a full configuration from a PAN-OS NGFW. This ' \
                             'will then be used to perform the validation.'
            label = 'Configuration'
            initial = self.get_value_from_workflow('config', '<xml></xml>')
            help_text = 'Paste the full XML configuration file to validate here.'
            config_field = fields.CharField(label=label, initial=initial, required=True,
                                            help_text=help_text,
                                            widget=widgets.Textarea(attrs={'cols': 40}))
            form.fields['config'] = config_field

        return form

    def form_valid(self, form):
        """
        form_valid is always called on a blank / new form, so this is essentially going to get called on every POST
        self.request.POST should contain all the variables defined in the service identified by the hidden field
        'service_id'
        :param form: blank form data from request
        :return: render of a success template after service is provisioned
        """
        snippet_name = self.get_value_from_workflow('snippet_name', '')
        mode = self.get_value_from_workflow('mode', 'online')

        if snippet_name == '':
            print('Could not find a valid meta-cnc def')
            raise SnippetRequiredException

        meta = db_utils.load_skillet_by_name(snippet_name)

        context = dict()
        self.header = 'Validation Results'
        context['header'] = self.header
        context['title'] = meta['label']
        context['base_html'] = self.base_html
        context['app_dir'] = self.app_dir
        context['view'] = self

        # Always grab all the default values, then update them based on user input in the workflow
        jinja_context = dict()
        if 'variables' in meta and type(meta['variables']) is list:
            for snippet_var in meta['variables']:
                jinja_context[snippet_var['name']] = snippet_var['default']

        # let's grab the current workflow values (values saved from ALL forms in this app
        jinja_context.update(self.get_workflow())

        if mode == 'online':
            # if we are in a workflow, then the input form was skipped and we are using the
            # values previously saved!
            workflow_name = self.request.session.get('workflow_name', False)

            if workflow_name:
                target_ip = self.get_value_from_workflow('TARGET_IP', '')
                # target_port = self.get_value_from_workflow('TARGET_PORT', 443)
                target_username = self.get_value_from_workflow('TARGET_USERNAME', '')
                target_password = self.get_value_from_workflow('TARGET_PASSWORD', '')

            else:
                # Grab the values from the form, this is always hard-coded in this class
                target_ip = self.request.POST.get('TARGET_IP', None)
                # target_port = self.request.POST.get('TARGET_IP', 443)
                target_username = self.request.POST.get('TARGET_USERNAME', None)
                target_password = self.request.POST.get('TARGET_PASSWORD', None)

                self.save_value_to_workflow('TARGET_IP', target_ip)
                # self.save_value_to_workflow('TARGET_PORT', target_port)
                self.save_value_to_workflow('TARGET_USERNAME', target_username)

            err_condition = False

            if target_ip is None or target_ip == '':
                form.add_error('TARGET_IP', 'Host entry cannot be blank')
                err_condition = True

            if target_username is None or target_username == '':
                form.add_error('TARGET_USERNAME', 'Username cannot be blank')
                err_condition = True

            if target_password is None or target_password == '':
                form.add_error('TARGET_PASSWORD', 'Password cannot be blank')
                err_condition = True

            if err_condition:
                return self.form_invalid(form)

            try:
                print(f'checking {target_ip} {target_username}')
                panoply = Panos(hostname=target_ip, api_username=target_username,
                                api_password=target_password, debug=True)

            except LoginException as le:
                print(le)
                form.add_error('TARGET_USERNAME', 'Invalid Credentials, ensure your username and password are correct')
                form.add_error('TARGET_PASSWORD', 'Invalid Credentials, ensure your username and password are correct')
                return self.form_invalid(form)
            except PanoplyException:
                form.add_error('TARGET_IP', 'Connection Refused Error, check the IP and try again')
                return self.form_invalid(form)

            if not panoply.connected:
                form.add_error('TARGET_IP', 'Connection Refused Error, check the IP and try again')
                return self.form_invalid(form)

        else:
            config = self.request.POST.get('config', '')
            self.save_value_to_workflow('config', config)
            panoply = None
            jinja_context['config'] = config

        try:
            skillet = PanValidationSkillet(meta, panoply)
            skillet_output = skillet.execute(jinja_context)
            validation_output = skillet_output.get('pan_validation', dict())

            # fix for #169 - add validation output to the context
            self.save_dict_to_workflow(validation_output)

            context['skillet'] = skillet
            context['results'] = validation_output

        except SkilletLoaderException:
            print("Could not load it for some reason")
            return render(self.request, 'pan_cnc/results.html', context)

        return render(self.request, 'panhandler/validation-results.html', context)


class ExportValidationResultsView(CNCBaseAuth, View):

    def get(self, request, *args, **kwargs) -> Any:

        validation_skillet = kwargs['skillet']
        meta = db_utils.load_skillet_by_name(validation_skillet)

        filename = meta.get('name', 'Validation Output')
        full_output = dict()

        full_context = self.get_workflow()

        for s in meta['snippets']:
            snippet_name = s['name']
            if snippet_name in full_context:
                output = full_context[snippet_name]
                full_output[snippet_name] = output

        json_output = json.dumps(full_output, indent=' ')
        response = HttpResponse(json_output, content_type="application/json")
        response['Content-Disposition'] = 'attachment; filename=%s.json' % filename
        return response


class FavoritesView(CNCView):
    template_name = "panhandler/favorites.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        favorites = Collection.objects.all()
        collections_info = dict()
        for f in favorites:
            collections_info[f.name] = dict()
            collections_info[f.name]['categories'] = json.dumps(f.categories)
            collections_info[f.name]['description'] = f.description

        context['collections'] = collections_info
        return context


class DeleteFavoriteView(CNCBaseAuth, RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        collection_name = kwargs['favorite']
        collection = Collection.objects.get(name=collection_name)
        collection.delete()
        return '/panhandler/favorites'


class AddFavoritesView(PanhandlerAppFormView):
    snippet = 'create_favorite'
    next_url = '/panhandler/favorites'
    app_dir = 'panhandler'
    header = "Favorites"
    title = "Add a new Collection"

    # once the form has been submitted and we have all the values placed in the workflow, execute this
    def form_valid(self, form):
        workflow = self.get_workflow()

        try:

            collection_name = workflow['collection_name']
            collection_description = workflow['collection_description']
            categories = workflow.get('collection_categories', '[]')

            c = Collection.objects.create(
                name=collection_name,
                description=collection_description,
                categories=categories
            )
            print(f'created new collection with id {c.id}')

            self.pop_value_from_workflow('collection_categories')
            self.pop_value_from_workflow('snippet_name')

        except KeyError:
            return self.form_invalid(form)

        return super().form_valid(form)


class FavoriteCollectionView(CNCView):
    template_name = "panhandler/favorite.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection = self.kwargs.get('favorite', '')

        skillet_ids = Favorite.objects.filter(collection__name=collection)

        skillets = list()
        for s in skillet_ids:
            skillet_dict = db_utils.load_skillet_by_name(s.skillet_id)
            skillets.append(skillet_dict)

        if not skillets:
            messages.add_message(self.request, messages.INFO,
                                 mark_safe('No Skillets have been added to this Favorite yet. '
                                           'Click on the <a href="/panhandler/collection/All Skillets" '
                                           'class="btn btn-outline-primary">'
                                           '<li class="fa fa-heart"></li></a> to add a Skillet.'))

        context['skillets'] = skillets
        context['collection'] = collection

        return context


class AddSkilletToFavoritesView(PanhandlerAppFormView):
    snippet = 'add_skillet_to_favorite'
    next_url = '/panhandler/favorites'
    app_dir = 'panhandler'
    header = "Favorites"
    title = "Add a new Collection"

    def get_context_data(self, **kwargs) -> dict:

        skillet_name = self.kwargs.get('skillet_name', '')
        all_favorites = Collection.objects.all()

        skillet = db_utils.load_skillet_by_name(skillet_name)

        if skillet is None:
            raise SnippetRequiredException('Could not find that skillet!')

        skillet_label = skillet.get('label', '')

        favorite_names = list()
        for favorite in all_favorites:
            favorite_names.append(favorite.name)

        if not favorite_names:
            messages.add_message(self.request, messages.WARNING,
                                 mark_safe("You have not yet added any favorites. Click "
                                           "<a href='/panhandler/add_favorite'>Add Favorite Now</a>"
                                           " to get started."))

        self.save_value_to_workflow('all_favorites', favorite_names)
        self.save_value_to_workflow('skillet_name', skillet_name)

        if Favorite.objects.filter(skillet_id=skillet_name).exists():
            favorite = Favorite.objects.get(skillet_id=skillet_name)
            current_favorites_qs = favorite.collection_set.all()
            current_favorites = list()
            for f in current_favorites_qs:
                current_favorites.append(f.name)

            self.prepopulated_form_values['favorites'] = current_favorites

        context = super().get_context_data(**kwargs)
        context['title'] = f'Add {skillet_label} to Favorites '
        context['header'] = 'Configure Favorites'

        return context

    # once the form has been submitted and we have all the values placed in the workflow, execute this
    def form_valid(self, form):
        workflow = self.get_workflow()

        try:
            skillet_name = workflow['skillet_name']
            favorites = workflow['favorites']

            # FIXME - should no longer be deleting skillets due to no favorites ...
            if not favorites:
                if Favorite.objects.filter(skillet_id=skillet_name).exists():
                    skillet = Favorite.objects.get(skillet_id=skillet_name)
                    skillet.collection_set.clear()
                    messages.add_message(self.request, messages.INFO, 'Removed Skillet from All Favorites')
                    self.next_url = self.request.session.get('last_page', '/')

                return super().form_valid(form)

            (skillet, created) = Favorite.objects.get_or_create(
                skillet_id=skillet_name
            )

            if not created:
                skillet.collection_set.clear()

            for f in favorites:
                c = Collection.objects.get(name=f)
                skillet.collection_set.add(c)

            self.pop_value_from_workflow('favorites')
            self.pop_value_from_workflow('skillet_name')

        except KeyError:
            return self.form_invalid(form)

        return super().form_valid(form)


class ExtractTemplateVariablesView(CNCBaseAuth, View):

    def post(self, request, *args, **kwargs) -> HttpResponse:

        template_str = 'not found'

        if self.request.is_ajax():
            try:
                json_str = self.request.body
                json_obj = json.loads(json_str)
                template_str = json_obj.get('template_str', 'not found')
            except ValueError:
                message = 'Could not parse input'
                return HttpResponse(message, content_type="application/json")

        sl = SkilletLoader()

        snippet = dict()
        snippet['name'] = 'template_snippet'
        snippet['element'] = template_str

        skillet_dict = dict()
        skillet_dict['name'] = 'template_skillet'
        skillet_dict['description'] = 'template'
        skillet_dict['snippets'] = [snippet]

        s = sl.normalize_skillet_dict(skillet_dict)

        skillet = TemplateSkillet(s)

        variables = skillet.get_declared_variables()
        json_output = json.dumps(variables)
        response = HttpResponse(json_output, content_type="application/json")
        return response


class SkilletTestView(CNCBaseAuth, View):

    def post(self, request, *args, **kwargs) -> HttpResponse:

        if self.request.is_ajax():
            try:
                json_str = self.request.body
                json_obj = json.loads(json_str)
                skillet_dict = json_obj.get('skillet', {})
                context = json_obj.get('context', {})

            except ValueError:
                message = 'Could not parse input'
                return HttpResponse(message, content_type="application/json")
        else:
            messages.add_message(self.request, messages.ERROR, 'Invalid Request Type')
            return HttpResponseRedirect('/panhandler')

        sl = SkilletLoader()

        skillet = sl.create_skillet(skillet_dict)

        if not str(skillet.type).startswith('pan'):
            response = HttpResponse(json.dumps({"error": "Invalid Skillet type"}), content_type="application/json")
            return response

        results = dict()
        output = dict()

        if len(skillet_dict['snippets']) == 1:
            # this is a single snippet execution - check for dangerous commands
            snippet = skillet.get_snippets()[0]
            if not snippet.should_execute(context):
                # skip initialize_context which will contact the device
                skillet.context = context
                output['debug'] = 'This snippet was skipped due to when conditional'
                output['metadata'] = dict()
                output['metadata']['name'] = snippet.metadata['name']
                output['metadata']['when'] = snippet.metadata['when']

            elif 'cmd' in snippet.metadata and \
                    snippet.metadata['cmd'] in ('op', 'set', 'edit', 'override', 'move', 'rename', 'clone', 'delete'):
                skillet.initialize_context(context)
                metadata = snippet.render_metadata(context)
                output['debug'] = 'Destructive action that would have been taken captured as metadata instead'
                output['metadata'] = metadata

            else:
                try:

                    output = skillet.execute(context)
                    if skillet_dict['type'] == 'pan_validation':
                        if snippet.name in skillet.context:
                            output['pan_validation'][snippet.name] = skillet.context[snippet.name]

                except PanoplyException as pe:
                    print(pe)
                    output = str(pe)
        else:
            try:

                output = skillet.execute(context)

            except PanoplyException as pe:
                print(pe)
                output = str(pe)

        results['output'] = output
        results['context'] = dict()

        # avoid putting full config var back into context
        for i in skillet.context:
            if i != 'config':
                results['context'][i] = skillet.context[i]

        json_output = json.dumps(results)
        response = HttpResponse(json_output, content_type="application/json")
        return response


class GenerateKeyView(CNCBaseAuth, View):

    def post(self, request, *args, **kwargs) -> HttpResponse:

        if self.request.is_ajax():
            try:
                json_str = self.request.body
                json_obj = json.loads(json_str)
                repo_name = json_obj.get('name', '')

            except ValueError:
                message = 'Could not parse input'
                return HttpResponse(message, content_type="application/json")
        else:
            message = 'invalid input'
            return HttpResponse(message, content_type="application/json")

        pub_key = git_utils.generate_ssh_key(repo_name)
        output = dict()
        output['pub'] = pub_key
        json_output = json.dumps(output)
        response = HttpResponse(json_output, content_type="application/json")
        return response


class PushGitRepositoryView(CNCBaseAuth, View):

    def post(self, request, *args, **kwargs) -> HttpResponse:

        if self.request.is_ajax():
            try:
                json_str = self.request.body
                json_obj = json.loads(json_str)
                repo_name = json_obj.get('name', '')

            except ValueError:
                message = 'Could not parse input'
                return HttpResponse(message, content_type="application/json")
        else:
            message = 'invalid input'
            return HttpResponse(message, content_type="application/json")

        if not RepositoryDetails.objects.filter(name=repo_name).exists():
            message = 'invalid repository'
            return HttpResponse(message, content_type="application/json")

        repo = RepositoryDetails.objects.get(name=repo_name)

        output = dict()

        if not repo.url.startswith('git@') and not repo.url.startswith('ssh://'):
            message = 'invalid Repository URL - Push requires an SSH URL'
            output['status'] = message
            return HttpResponse(json.dumps(output), content_type="application/json")

        user_dir = os.path.expanduser('~/.pan_cnc')
        snippets_dir = os.path.join(user_dir, 'panhandler/repositories')
        repo_dir = os.path.join(snippets_dir, repo_name)

        (success, msg) = git_utils.push_local_changes(repo_dir, repo.deploy_key_path)

        if success:
            output['status'] = 'Changes pushed upstream'
            messages.add_message(self.request, messages.SUCCESS, 'Changes pushed upstream')
        else:
            output['status'] = f'Error pushing changes upstream\n{msg}'

        json_output = json.dumps(output)
        response = HttpResponse(json_output, content_type="application/json")
        return response
