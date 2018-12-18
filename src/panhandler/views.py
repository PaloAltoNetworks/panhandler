import os

from django.conf import settings
from django.views.generic.base import RedirectView

from pan_cnc.lib.actions.DockerAction import DockerAction
from pan_cnc.lib import git_utils

from pan_cnc.views import *
from pathlib import Path
from itertools import islice

from django.contrib import messages


class ImportRepoView(CNCBaseFormView):
    # define initial dynamic form from this snippet metadata
    snippet = 'import_repo'
    next_url = '/panhandler/provision'

    # once the form has been submitted and we have all the values placed in the workflow, execute this
    def form_valid(self, form):
        workflow = self.get_workflow()

        # this will use the git docker container so we don't have to worry about installing anything
        # standardize on alpine as much as possible
        docker_image = 'alpine/git'

        # get the values from the user submitted form here
        url = workflow.get('url')
        branch = workflow.get('branch')
        repo_name = workflow.get('repo_name')
        # FIXME - Ensure repo_name is unique

        # we are going to keep the snippets in the snippets dir in the panhandler app
        # get the dir where all apps are installed
        src_dir = settings.SRC_PATH
        # get the panhandler app dir
        panhandler_dir = os.path.join(src_dir, 'panhandler')
        # get the snippets dir under that
        snippets_dir = os.path.join(panhandler_dir, 'snippets')
        # figure out what our new repo / snippet dir will be
        new_repo_snippets_dir = os.path.join(snippets_dir, repo_name)

        # create our docker command to pass to git
        docker_cmd = f'clone --config http.sslVerify=false -b {branch} --depth 3 \
        --shallow-submodules {url} /git'

        # create our generc docker client
        docker_client = DockerAction()
        docker_client.docker_image = docker_image
        docker_client.docker_cmd = docker_cmd
        docker_client.storage_dir = repo_name
        docker_client.persistent_dir = snippets_dir

        docker_client.working_dir = '/git'
        docker_client.template_name = ''

        r = docker_client.execute_template(template='')

        context = dict()
        context['results'] = r
        return render(self.request, 'pan_cnc/results.html', context)


class ListReposView(CNCView):
    template_name = 'panhandler/repos.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        snippets_dir = Path(os.path.join(settings.SRC_PATH, 'panhandler', 'snippets'))
        repos = list()
        for d in snippets_dir.rglob('./*'):
            print(d)
            git_dir = os.path.join(d, '.git')
            if os.path.isdir(git_dir):
                repo_name = os.path.basename(d)
                repo_detail = git_utils.get_repo_details(repo_name, d)
                repos.append(repo_detail)

        context['repos'] = repos
        return context


class RepoDetailsView(CNCView):
    template_name = 'panhandler/repo_detail.html'
    # define initial dynamic form from this snippet metadata

    def get_context_data(self, **kwargs):

        repo_name = self.kwargs['repo_name']

        # we are going to keep the snippets in the snippets dir in the panhandler app
        # get the dir where all apps are installed
        src_dir = settings.SRC_PATH
        # get the panhandler app dir
        panhandler_dir = os.path.join(src_dir, 'panhandler')
        # get the snippets dir under that
        snippets_dir = os.path.join(panhandler_dir, 'snippets')
        repo_dir = os.path.join(snippets_dir, repo_name)
        repo_detail = git_utils.get_repo_details(repo_name, repo_dir)

        # create our docker command to pass to git
        context = dict()
        context['repo_detail'] = repo_detail
        context['repo_name'] = repo_name
        return context


class UpdateRepoView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        repo_name = kwargs['repo_name']
        # we are going to keep the snippets in the snippets dir in the panhandler app
        # get the dir where all apps are installed
        src_dir = settings.SRC_PATH
        # get the panhandler app dir
        panhandler_dir = os.path.join(src_dir, 'panhandler')
        # get the snippets dir under that
        snippets_dir = os.path.join(panhandler_dir, 'snippets')
        repo_dir = os.path.join(snippets_dir, repo_name)

        msg = git_utils.update_repo(repo_dir)
        if 'Error' in msg:
            level = messages.ERROR
        else:
            level = messages.INFO

        messages.add_message(self.request, level, msg)
        return f'/panhandler/repo_detail/{repo_name}'


class ListSnippetGroupsView(CNCView):
    template_name = 'panhandler/snippet_groups.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        print('Getting all snippets')
        all_snippets = snippet_utils.load_snippets_of_type(snippet_type=None, app_dir='panhandler')
        snippets_by_group = dict()
        for snippet in all_snippets:
            print('checking snippet: %s' % snippet['name'])
            if 'labels' in snippet and 'service_type' in snippet['labels']:
                group = snippet['labels']['service_type']
                snippets_by_group[group] = snippet

        context['snippets'] = snippets_by_group
        return context


class ListSnippetsByGroup(CNCBaseAuth, CNCBaseFormView):
    next_url = '/panhandler/provision'

    def get_snippet(self):
        print('Getting snippet here in get_snippet RIGHT HERE')
        if 'snippet_name' in self.request.POST:
            print('FOUND IT RIGHT HERE')
            snippet_name = self.request.POST['snippet_name']
            print(snippet_name)
            return snippet_name
        else:
            print('what happened here? WTF')
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
        snippet_group = self.kwargs['service_type']
        print(snippet_group)

        context = super().get_context_data(**kwargs)

        context['title'] = 'All snippets in group: %s' % snippet_group
        context['header'] = 'Snippet Library'
        services = snippet_utils.load_snippets_by_label('service_type', snippet_group, self.app_dir)

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
        new_choices_field = forms.ChoiceField(choices=choices_set, label='Choose Snippet:')
        # set it on the original form, overwriting the hardcoded GSB version

        form.fields['snippet_name'] = new_choices_field

        context['form'] = form
        return context
