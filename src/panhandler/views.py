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
Palo Alto Networks panos- bootstrapper

panhandler is a tool to find, download, and use CCF enabled repositories

Please see http://panhandler.readthedocs.io for more information

This software is provided without support, warranty, or guarantee.
Use at your own risk.
"""
import os
import shutil
from pathlib import Path

from django.conf import settings

from pan_cnc.lib import git_utils
from pan_cnc.views import *
from panhandler.lib import app_utils


class ImportRepoView(CNCBaseFormView):
    # define initial dynamic form from this snippet metadata
    snippet = 'import_repo'
    next_url = '/provision'
    template_name = 'panhandler/import_repo.html'

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
        # FIXME - Ensure repo_name is unique

        # # we are going to keep the snippets in the snippets dir in the panhandler app
        # # get the dir where all apps are installed
        # src_dir = settings.SRC_PATH
        # # get the panhandler app dir
        # panhandler_dir = os.path.join(src_dir, 'panhandler')
        # # get the snippets dir under that
        # snippets_dir = os.path.join(panhandler_dir, 'snippets')
        # # figure out what our new repo / snippet dir will be
        # new_repo_snippets_dir = os.path.join(snippets_dir, repo_name)

        user_dir = os.path.expanduser('~/.pan_cnc')
        snippets_dir = os.path.join(user_dir, 'panhandler/repositories')
        repo_dir = os.path.join(snippets_dir, repo_name)

        if os.path.exists(repo_dir):
            messages.add_message(self.request, messages.ERROR, 'A Repository with this name already exists')
            return HttpResponseRedirect('repos')
        else:
            os.makedirs(repo_dir)

        # where to clone from
        clone_url = url
        if 'github' in url.lower():
            details = git_utils.get_repo_upstream_details(repo_name, url)
            if 'clone_url' in details:
                clone_url = details['clone_url']

        if not git_utils.clone_repo(repo_dir, repo_name, clone_url, branch):
            messages.add_message(self.request, messages.ERROR, 'Could not Import Repository')
        else:
            print('Invalidating snippet cache')
            snippet_utils.invalidate_snippet_caches()

            messages.add_message(self.request, messages.INFO, 'Imported Repository Successfully')

        # return render(self.request, 'pan_cnc/results.html', context)
        return HttpResponseRedirect('repos')


class ListReposView(CNCView):
    template_name = 'panhandler/repos.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        # snippets_dir = Path(os.path.join(settings.SRC_PATH, 'panhandler', 'snippets'))

        snippets_dir = Path(os.path.join(os.path.expanduser('~/.pan_cnc'), 'panhandler', 'repositories'))

        repos = list()
        for d in snippets_dir.rglob('./*'):
            # git_dir = os.path.join(d, '.git')
            git_dir = d.joinpath('.git')
            if git_dir.exists() and git_dir.is_dir():
                repo_detail = git_utils.get_repo_details(d.name, d)
                repos.append(repo_detail)
                continue

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

        repo_detail = git_utils.get_repo_details(repo_name, repo_dir)

        try:
            snippets_from_repo = snippet_utils.load_snippets_of_type_from_dir(repo_dir)
        except CCFParserError:
            messages.add_message(self.request, messages.ERROR, 'Could not read all snippets from repo. Parser error')
            snippets_from_repo = list()

        # create our docker command to pass to git
        context = super().get_context_data(**kwargs)
        context['repo_detail'] = repo_detail
        context['repo_name'] = repo_name
        context['snippets'] = snippets_from_repo
        return context


class UpdateRepoView(CNCBaseAuth, RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        repo_name = kwargs['repo_name']
        # we are going to keep the snippets in the snippets dir in the panhandler app
        # get the dir where all apps are installed
        src_dir = settings.SRC_PATH
        # get the panhandler app dir
        # panhandler_dir = os.path.join(src_dir, 'panhandler')
        # # get the snippets dir under that
        # snippets_dir = os.path.join(panhandler_dir, 'snippets')
        # repo_dir = os.path.join(snippets_dir, repo_name)

        user_dir = os.path.expanduser('~')
        repo_dir = os.path.join(user_dir, '.pan_cnc', 'panhandler', 'repositories', repo_name)

        msg = git_utils.update_repo(repo_dir)
        if 'Error' in msg:
            level = messages.ERROR
        else:
            print('Invalidating snippet cache')
            snippet_utils.invalidate_snippet_caches()
            cnc_utils.set_long_term_cached_value(f'{repo_name}_detail', dict(), 0)

            level = messages.INFO

        messages.add_message(self.request, level, msg)
        return f'/panhandler/repo_detail/{repo_name}'


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
            shutil.rmtree(repo_dir)
            print('Invalidating snippet cache')
            snippet_utils.invalidate_snippet_caches()
            cnc_utils.set_long_term_cached_value(f'{repo_name}_detail', dict(), 0)

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
        collections.append('Kitchen Sink')
        context['collections'] = collections

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
