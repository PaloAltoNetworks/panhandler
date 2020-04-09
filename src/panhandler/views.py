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
import shutil
from pathlib import Path

from django.conf import settings
from skilletlib.exceptions import SkilletLoaderException
from skilletlib.skillet.pan_validation import PanValidationSkillet

from pan_cnc.lib import git_utils
from pan_cnc.lib.exceptions import ImportRepositoryException
from pan_cnc.views import *
from panhandler.lib import app_utils


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
        return context


class ImportRepoView(CNCBaseFormView):
    # define initial dynamic form from this snippet metadata
    snippet = 'import_repo'
    next_url = '/provision'
    template_name = 'panhandler/import_repo.html'
    app_dir = 'panhandler'

    def get_snippet(self):
        return self.snippet

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

            except PermissionError as pe:
                messages.add_message(self.request, messages.ERROR,
                                     'Could not create repository directory, Permission Denied')
                return HttpResponseRedirect('repos')
            except OSError as ose:
                messages.add_message(self.request, messages.ERROR,
                                     'Could not create repository directory')
                return HttpResponseRedirect('repos')

        # where to clone from
        clone_url = url.strip()
        if 'github' in url.lower():
            details = git_utils.get_repo_upstream_details(repo_name, url, self.app_dir)
            if 'clone_url' in details:
                clone_url = details['clone_url']

        try:
            message = git_utils.clone_repository(repo_dir, repo_name, clone_url)
            print(message)
        except ImportRepositoryException as ire:
            messages.add_message(self.request, messages.ERROR, f'Could not Import Repository: {ire}')
        else:
            print('Invalidating snippet cache')
            snippet_utils.invalidate_snippet_caches(self.app_dir)

            # no need to evict all these items, just grab the new repo details and append it to list and re-cache
            # cnc_utils.evict_cache_items_of_type(self.app_dir, 'imported_git_repos')
            repos = cnc_utils.get_long_term_cached_value(self.app_dir, 'imported_repositories')

            # FIX for #148
            if repos is None:
                repos = list()

            repo_detail = git_utils.get_repo_details(repo_name, repo_dir, self.app_dir)
            repos.append(repo_detail)
            cnc_utils.set_long_term_cached_value(self.app_dir, 'imported_repositories', repos, 604800,
                                                 'imported_git_repos')

            debug_errors = snippet_utils.debug_snippets_in_repo(Path(repo_dir), list())

            # check each snippet found for dependencies
            loaded_skillets = snippet_utils.load_snippets_of_type_from_dir(self.app_dir, repo_dir)
            for skillet in loaded_skillets:
                for depends in skillet['depends']:
                    url = depends.get('url', None)
                    name = depends.get('name', None)
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

        # return render(self.request, 'pan_cnc/results.html', context)
        return HttpResponseRedirect('repos')


class ListReposView(CNCView):
    template_name = 'panhandler/repos.html'
    app_dir = 'panhandler'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        # snippets_dir = Path(os.path.join(settings.SRC_PATH, 'panhandler', 'snippets'))

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
            print(f'Returning cached repos')
            context['repos'] = repos

        else:
            repos = list()

            for d in snippets_dir.iterdir():
                # git_dir = os.path.join(d, '.git')
                git_dir = d.joinpath('.git')

                if git_dir.exists() and git_dir.is_dir():
                    repo_detail = git_utils.get_repo_details(d.name, d, self.app_dir)
                    repos.append(repo_detail)
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

    # define initial dynamic form from this snippet metadata

    def get_context_data(self, **kwargs):
        repo_name = self.kwargs['repo_name']

        # we are going to keep the snippets in the snippets dir in the panhandler app
        # get the dir where all apps are installed
        src_dir = settings.SRC_PATH
        # get the panhandler app dir
        panhandler_dir = os.path.join(src_dir, 'panhandler')
        # get the snippets dir under that
        # snippets_dir = os.path.join(panhandler_dir, 'snippets')
        # repo_dir = os.path.join(snippets_dir, repo_name)

        user_dir = os.path.expanduser('~')
        repo_dir = os.path.join(user_dir, '.pan_cnc', 'panhandler', 'repositories', repo_name)

        if os.path.exists(repo_dir):
            repo_detail = git_utils.get_repo_details(repo_name, repo_dir, self.app_dir)

        else:
            repo_detail = dict()
            repo_detail['name'] = 'repo_name'
            repo_detail['error'] = 'Repository directory not found'

        if 'error' in repo_detail:
            messages.add_message(self.request, messages.ERROR, repo_detail['error'])

        try:
            snippets_from_repo = snippet_utils.load_snippets_of_type_from_dir(self.app_dir, repo_dir)

        except CCFParserError:
            messages.add_message(self.request, messages.ERROR, 'Could not read all snippets from repo. Parser error')
            snippets_from_repo = list()

        # get a list of all collections found in this repo
        collections = list()
        for skillet in snippets_from_repo:
            if 'labels' in skillet and 'collection' in skillet['labels']:
                collection = skillet['labels']['collection']

                if type(collection) is str:
                    if collection not in collections:
                        collections.append(collection)

                elif type(collection) is list:
                    for collection_member in collection:
                        if collection_member not in collections:
                            collections.append(collection_member)

        # create our docker command to pass to git
        context = super().get_context_data(**kwargs)
        context['repo_detail'] = repo_detail
        context['repo_name'] = repo_name
        context['snippets'] = snippets_from_repo
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

        msg = git_utils.update_repo(repo_dir, branch)

        if 'Error' in msg:
            level = messages.ERROR
            cnc_utils.evict_cache_items_of_type(self.app_dir, 'imported_git_repos')

        elif 'updated' in msg or 'Checked out new' in msg:
            # msg updated will catch both switching branches as well as new commits
            # since this repoo has been updated, we need to ensure the caches are all in sync
            print('Invalidating snippet cache')
            snippet_utils.invalidate_snippet_caches(self.app_dir)
            git_utils.update_repo_in_cache(repo_name, repo_dir, self.app_dir)

            # remove all python3 init touch files if there is an update
            task_utils.python3_reset_init(repo_dir)

            level = messages.INFO
        else:
            level = messages.INFO

        messages.add_message(self.request, level, msg)

        # check if there are new branches available
        repo_detail = git_utils.get_repo_details(repo_name, repo_dir, self.app_dir)
        repo_branches = git_utils.get_repo_branches_from_dir(repo_dir)
        if repo_detail['branches'] != repo_branches:
            messages.add_message(self.request, messages.INFO, 'New Branches are available')
            git_utils.update_repo_in_cache(repo_name, repo_dir, self.app_dir)

        # check each snippet found for dependencies
        repos = cnc_utils.get_long_term_cached_value(self.app_dir, 'imported_repositories')
        loaded_skillets = snippet_utils.load_snippets_of_type_from_dir(self.app_dir, repo_dir)
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

        if not err_condition:
            repos = ", ".join(updates)
            messages.add_message(self.request, messages.SUCCESS, f'Successfully Updated repositories: {repos}')

        cnc_utils.evict_cache_items_of_type(self.app_dir, 'imported_git_repos')
        snippet_utils.invalidate_snippet_caches(self.app_dir)
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

            print('Invalidating snippet cache')
            snippet_utils.invalidate_snippet_caches(self.app_dir)
            cnc_utils.set_long_term_cached_value(self.app_dir, f'{repo_name}_detail', None, 0, 'snippet')
            cnc_utils.evict_cache_items_of_type(self.app_dir, 'imported_git_repos')

        messages.add_message(self.request, messages.SUCCESS, 'Repo Successfully Removed')
        return f'/panhandler/repos'


class ListSnippetTypesView(CNCView):
    app_dir = 'panhandler'
    template_name = 'panhandler/snippet_types.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print('Getting all snippets')
        panos_snippets = snippet_utils.load_snippets_of_type(snippet_type='panos', app_dir='panhandler')
        panorama_snippets = snippet_utils.load_snippets_of_type(snippet_type='panorama', app_dir='panhandler')
        panorama_gpcs_snippets = snippet_utils.load_snippets_of_type(snippet_type='panorama-gpcs', app_dir='panhandler')
        template_snippets = snippet_utils.load_snippets_of_type(snippet_type='template', app_dir='panhandler')
        terraform_templates = snippet_utils.load_snippets_of_type(snippet_type='terraform', app_dir='panhandler')

        snippets_by_type = dict()
        if len(panos_snippets):
            snippets_by_type['PAN-OS'] = panos_snippets
        if len(panorama_snippets):
            snippets_by_type['Panorama'] = panorama_snippets
        if len(panorama_gpcs_snippets):
            snippets_by_type['Panorama-GPCS'] = panorama_gpcs_snippets
        if len(template_snippets):
            snippets_by_type['Templates'] = template_snippets
        if len(terraform_templates):
            snippets_by_type['Terraform'] = terraform_templates

        context['snippets'] = snippets_by_type

        return context


class ListSnippetsByGroup(CNCBaseFormView):
    next_url = '/provision'
    app_dir = 'panhandler'

    def get_snippet(self):
        print('Getting snippet from POST here in ListSnippetByGroup:get_snippet')
        if 'snippet_name' in self.request.POST:
            print('Found meta-cnc in POST')
            snippet_name = self.request.POST['snippet_name']
            print(snippet_name)
            return snippet_name
        else:
            print('what happened here?')
            return self.snippet

    def save_workflow_to_session(self) -> None:
        """
        Save the current user input to the session
        :return: None
        """

        if self.app_dir in self.request.session:
            current_workflow = self.request.session[self.app_dir]
        else:
            current_workflow = dict()

        # there is not service here, override with hard coded snippet_name value
        var_name = 'snippet_name'
        if var_name in self.request.POST:
            print('Adding variable %s to session' % var_name)
            current_workflow[var_name] = self.request.POST.get(var_name)

        self.request.session[self.app_dir] = current_workflow

    def get_context_data(self, **kwargs):
        snippet_type = self.kwargs['service_type']
        print(snippet_type)

        context = super().get_context_data(**kwargs)

        snippet_labels = dict()
        snippet_labels['PAN-OS'] = 'panos'
        snippet_labels['Panorama'] = 'panorama'
        snippet_labels['Panorama-GPCS'] = 'panorama-gpcs'
        snippet_labels['Templates'] = 'template'
        snippet_labels['Terraform'] = 'terraform'

        context['title'] = 'All Templates with type: %s' % snippet_type
        context['header'] = 'Template Library'
        services = snippet_utils.load_snippets_of_type(snippet_labels[snippet_type], self.app_dir)

        form = context['form']

        # we need to construct a new ChoiceField with the following basic format
        # snippet_name = forms.ChoiceField(choices=(('gold', 'Gold'), ('silver', 'Silver'), ('bronze', 'Bronze')))
        choices_list = list()
        # grab each service and construct a simple tuple with name and label, append to the list
        for service in services:
            choice = (service['name'], service['label'])
            choices_list.append(choice)

        # let's sort the list by the label attribute (index 1 in the tuple)
        choices_list = sorted(choices_list, key=lambda k: k[1])
        # convert our list of tuples into a tuple itself
        choices_set = tuple(choices_list)
        # make our new field
        new_choices_field = forms.ChoiceField(choices=choices_set, label='Choose Template:')
        # set it on the original form, overwriting the hardcoded GSB version

        form.fields['snippet_name'] = new_choices_field

        context['form'] = form
        return context


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
        collections = snippet_utils.load_all_label_values(self.app_dir, 'collection')

        # build dict of collections related to other collections (if any)
        # and a count of how many skillets are in the collection
        collections_info = dict()

        # manually create a collection called 'All'
        all_skillets = 'All Skillets'

        # get the full list of all snippets
        all_snippets = snippet_utils.load_all_snippets(self.app_dir)

        collections_info[all_skillets] = dict()
        collections_info[all_skillets]['count'] = len(all_snippets)
        collections_info[all_skillets]['related'] = list()

        # iterate over the list of collections
        for c in collections:
            if c not in collections_info:
                collections_info[c] = dict()
                collections_info[c]['count'] = 0

            skillets = snippet_utils.load_snippets_by_label('collection', c, self.app_dir)
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
            skillets = snippet_utils.load_all_snippets(self.app_dir)
        else:
            skillets = snippet_utils.load_snippets_by_label('collection', collection, self.app_dir)

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


class CheckAppUpdateView(CNCBaseAuth, RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        cnc_utils.evict_cache_items_of_type('panhandler', 'app_update')
        return '/'


# Validation Testing Class below
class ExecuteValidationSkilletView(ProvisionSnippetView):
    header = 'Configure Validation Skillet'

    def generate_dynamic_form(self, data=None) -> forms.Form:
        dynamic_form = super().generate_dynamic_form(data)
        choices_list = [('offline', 'Offline'), ('online', 'Online')]
        description = 'Validation Mode'
        mode = self.get_value_from_workflow('mode', 'online')
        default = mode
        required = True
        help_text = 'Online mode will pull configuration directly from an accessible PAN-OS device. Offline ' \
                    'allows an XML configuration file to be uploaded.'
        dynamic_form.fields['mode'] = forms.ChoiceField(choices=choices_list,
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
            workflow_skillet_dict = snippet_utils.load_snippet_with_name(workflow_name, self.app_dir)
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
                self.meta = snippet_utils.load_snippet_with_name(snippet, self.app_dir)

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

    def generate_dynamic_form(self, data=None) -> forms.Form:

        form = forms.Form(data=data)

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
            target_port_label = 'Target Port'
            target_username_label = 'Target Username'
            target_password_label = 'Target Password'

            target_ip = self.get_value_from_workflow('TARGET_IP', '')
            # target_port = self.get_value_from_workflow('TARGET_PORT', 443)
            target_username = self.get_value_from_workflow('TARGET_USERNAME', '')
            target_password = self.get_value_from_workflow('TARGET_PASSWORD', '')

            target_ip_field = forms.CharField(label=target_ip_label, initial=target_ip, required=True,
                                              validators=[FqdnOrIp])
            target_username_field = forms.CharField(label=target_username_label, initial=target_username, required=True)
            target_password_field = forms.CharField(widget=forms.PasswordInput(render_value=True), required=True,
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
            config_field = forms.CharField(label=label, initial=initial, required=True,
                                           help_text=help_text,
                                           widget=forms.Textarea(attrs={'cols': 40}))
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

        meta = snippet_utils.load_snippet_with_name(snippet_name, self.app_dir)

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
            except PanoplyException as pe:
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
            results = list()
            skillet_output = skillet.execute(jinja_context)
            validation_output = skillet_output.get('pan_validation', dict())
            for snippet in skillet.snippet_stack:
                name = snippet.get('name', '')
                cmd = snippet.get('cmd', '')
                if cmd != 'validate':
                    print('skipping non-validation snippet')
                    continue

                result_object = dict()
                if snippet['name'] in validation_output:
                    result_object['name'] = name
                    result_object['results'] = validation_output[name]
                else:
                    result_object['name'] = name
                    result_object['results'] = {}

                results.append(result_object)

            context['results'] = results

        except SkilletLoaderException:
            print(f"Could not load it for some reason")
            return render(self.request, 'pan_cnc/results.html', context)

        return render(self.request, 'panhandler/validation-results.html', context)
