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
        branch = workflow.get('branch')
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
            message = git_utils.clone_repository(repo_dir, repo_name, clone_url, branch)
            print(message)
        except ImportRepositoryException as ire:
            messages.add_message(self.request, messages.ERROR, f'Could not Import Repository: {ire}')
        else:
            print('Invalidating snippet cache')
            snippet_utils.invalidate_snippet_caches(self.app_dir)
            cnc_utils.evict_cache_items_of_type(self.app_dir, 'imported_git_repos')

            debug_errors = snippet_utils.debug_snippets_in_repo(Path(repo_dir), list())
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
            repo_detail['name'] = 'Repository directory not found'

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
        user_dir = os.path.expanduser('~')
        repo_dir = os.path.join(user_dir, '.pan_cnc', 'panhandler', 'repositories', repo_name)

        if not os.path.exists(repo_dir):
            messages.add_message(self.request, messages.ERROR, 'Repository directory does not exist!')
            return f'/panhandler/repo_detail/{repo_name}'

        msg = git_utils.update_repo(repo_dir)
        if 'Error' in msg:
            level = messages.ERROR
            cnc_utils.evict_cache_items_of_type(self.app_dir, 'imported_git_repos')
        elif 'Updated' in msg:
            print('Invalidating snippet cache')
            snippet_utils.invalidate_snippet_caches(self.app_dir)
            cnc_utils.set_long_term_cached_value(self.app_dir, f'{repo_name}_detail', None, 0, 'git_repo_details')
            level = messages.INFO
        else:
            level = messages.INFO

        messages.add_message(self.request, level, msg)

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
                msg = git_utils.update_repo(d)
                if 'Error' in msg:
                    print(f'Error updating Repository: {d.name}')
                    print(msg)
                    messages.add_message(self.request, messages.ERROR, f'Could not update repository {d.name}')
                    err_condition = True
                elif 'Updated' in msg:
                    print(f'Updated Repository: {d.name}')
                    updates.append(d.name)
                    cnc_utils.set_long_term_cached_value(self.app_dir, f'{d.name}_detail', None, 0, 'git_repo_details')

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
        print('Getting all labels')
        collections = snippet_utils.load_all_label_values(self.app_dir, 'collection')

        collections_info = dict()
        # build dict of collections related to other collections (if any)

        for c in collections:
            if c not in collections_info:
                collections_info[c] = dict()
                collections_info[c]['count'] = 0

            skillets = snippet_utils.load_snippets_by_label('collection', c, self.app_dir)
            collections_info[c]['count'] = len(skillets)
            related = list()
            # related.append(c)

            for skillet in skillets:
                if 'labels' in skillet and 'collection' in skillet['labels']:
                    if type(skillet['labels']['collection']) is list:
                        for related_collection in skillet['labels']['collection']:
                            if related_collection != c and related_collection not in related:
                                related.append(related_collection)

            collections_info[c]['related'] = json.dumps(related)

        collections.append('Kitchen Sink')
        context['collections'] = collections
        context['collections_info'] = collections_info

        return context


class ListSkilletsInCollectionView(CNCView):
    template_name = 'panhandler/collection.html'
    app_dir = 'panhandler'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        collection = self.kwargs.get('collection', 'Kitchen Sink')
        print(f'Getting all snippets with collection label {collection}')
        if collection == 'Kitchen Sink':
            skillets = snippet_utils.load_all_snippets_without_label_key(self.app_dir, 'collection')
        else:
            skillets = snippet_utils.load_snippets_by_label('collection', collection, self.app_dir)

        order_index = 1000
        for skillet in skillets:
            if 'order' not in skillet['labels']:
                skillet['labels']['order'] = order_index
                order_index += 1

        context['skillets'] = skillets
        context['collection'] = collection

        return context


class ViewSkilletView(ProvisionSnippetView):

    def get_snippet(self):
        """
        Override the get_snippet as the snippet_name is passed as a kwargs param and not a POST or in the session
        :return: name of the skillet found in the kwargs
        """
        skillet = self.kwargs.get('skillet', '')
        self.save_value_to_workflow('snippet_name', skillet)
        return skillet


class CheckAppUpdateView(CNCBaseAuth, RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        cnc_utils.evict_cache_items_of_type('panhandler', 'app_update')
        return '/'
