from collections import OrderedDict

import oyaml
import requests
from requests import ConnectionError

from pan_cnc.lib import cnc_utils


def get_recommended_links() -> list:
    app_name = 'panhandler'
    app_config = cnc_utils.get_app_config('panhandler')
    recommended_links = list()

    # do not make external calls if we are testing
    if cnc_utils.is_testing():
        print('Returning blank recommended links due to testing env')
        return recommended_links

    if 'application_data' not in app_config:
        print('Could not find application_data in .pan-cnc.yaml')
        return recommended_links

    if type(app_config['application_data']) is not dict:
        print('malformed application_data in .pan-cnc.yaml')
        return recommended_links

    if 'recommended_repos_link' not in app_config['application_data']:
        print('Could not find value recommended_repos_link key in application_data')
        return recommended_links

    recommend_url = app_config['application_data']['recommended_repos_link']

    if not str(recommend_url).startswith('http'):
        print('recommended_repos_link does not appear to be a valid link')
        return recommended_links

    try:
        # try to pull from cache is possible
        recommends_from_cache = cnc_utils.get_long_term_cached_value(app_name, 'recommended_links')
        if recommends_from_cache is not None:
            print('Returning recommended_links from the cache')
            return recommends_from_cache

        resp = requests.get(recommend_url, verify=False)
        if resp.status_code != 200:
            print('Could not fetch recommended_repos_link')
            print(resp.text)
            print(resp.status_code)
            return recommended_links

        data_object = oyaml.safe_load(resp.text)
        if _validate_recommended_data(data_object):
            # save for later
            cnc_utils.set_long_term_cached_value(app_name, 'recommended_links', data_object['links'], 7200,
                                                 'recommended_links')
            return data_object['links']
        else:
            # FIXME - return a default list here
            return recommended_links
    except ValueError as ve:
        print('Could not load response')
        return recommended_links

    except ConnectionError as ce:
        print('Could not fetch recommended links url')
        print(ce)
        return recommended_links


def _validate_recommended_data(data: OrderedDict) -> bool:
    """
    Ensure the returned data has the following structure:
    links:
      - name: Global Protect Skillets
        link: https://github.com/PaloAltoNetworks/GPSkillets
        branch: 90dev
        description: Configuration templates for GlobalProtect mobile users
    :param data: loaded object from oyaml.safe_load
    :return: boolean
    """

    if 'links' not in data:
        print('No links key in data')
        return False

    if type(data['links']) is not list:
        print('links is not a valid list!')
        return False

    for link in data['links']:
        if type(link) is not OrderedDict and type(link) is not dict:
            print('link entry is not a dict')
            return False

        if 'name' not in link or 'link' not in link or 'description' not in link:
            print('link entry does not have all required keys')
            return False
        
    return True

#
# def get_imported_git_repos():
#     snippets_dir = Path(os.path.join(settings.SRC_PATH, 'panhandler', 'snippets'))
#     repos = list()
#     for d in snippets_dir.rglob('./*'):
#         # git_dir = os.path.join(d, '.git')
#         git_dir = d.joinpath('.git')
#         if git_dir.exists() and git_dir.is_dir():
#             print(d)
#             repo_name = os.path.basename(d.name)
#             repo_detail = git_utils.get_repo_details(repo_name, d)
#             repos.append(repo_detail)
#             continue
#
#     return repos
