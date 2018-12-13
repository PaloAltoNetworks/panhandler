import os

from django.conf import settings

from pan_cnc.lib.actions.DockerAction import DockerAction
from pan_cnc.views import *


class ImportRepoView(CNCBaseFormView):
    # define initial dynamic form from this snippet metadata
    snippet = 'import_repo'

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
        docker_cmd = f'clone --config http.sslVerify=false -b {branch} --depth 1 \
        --shallow-submodules {url} /git'

        template = snippet_utils.render_snippet_template(self.service, self.app_dir, workflow)

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
