import os
from collections import OrderedDict
from datetime import datetime

import oyaml
import requests
from requests import ConnectionError, Timeout

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

        resp = requests.get(recommend_url, verify=False, timeout=5)
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
        print(ve)
        return recommended_links

    except ConnectionError as ce:
        print('Could not fetch recommended links url')
        print(ce)
        return recommended_links
    except Timeout as te:
        print('Timed out waiting for recommended links to load')
        print(te)
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


def is_up_to_date() -> (bool, None):
    """
    Attempts to gather current image tag and build date and compare with latest updated information in docker hub
    :return: True if we are up to date, False if there is a newer image, and None on error
    """

    current_build_time = _get_current_build_time()
    if not current_build_time:
        print('Could not determine if we are up to date!')
        return None

    current_tag = _get_current_tag()
    if not current_tag:
        print('Could not determine current tag!')
        return None

    image_data = _get_panhandler_image_data()
    if not image_data:
        print('Could not get image tag detail from docker hub!')
        return None

    try:
        for result in image_data['results']:
            if result['name'] == current_tag:
                last_updated_string = result['last_updated']
                last_updated = datetime.strptime(last_updated_string, '%Y-%m-%dT%H:%M:%S.%fZ')
                if last_updated > current_build_time:
                    delta = last_updated - current_build_time
                    if delta.total_seconds() > 60:
                        return False

        return True
    except ValueError as ve:
        print('Could not parse last updated value')
        print(ve)
        return None
    except KeyError as ke:
        print('unexpected data from docker hub API')
        print(ke)
        return None


def _get_current_build_time() -> (datetime, None):
    build_date_string = cnc_utils.get_long_term_cached_value('panhandler', 'current_build_time')

    if not build_date_string:
        print('Getting updated build_date_String')
        panhandler_config = cnc_utils.get_app_config('panhandler')
        if 'app_dir' not in panhandler_config:
            return None

        build_file = os.path.join(panhandler_config['app_dir'], 'build_date')

        if not os.path.exists(build_file) or not os.path.isfile(build_file):
            return None

        try:
            with open(build_file, 'r') as bf:
                build_date_string = str(bf.readline()).strip()
                cnc_utils.set_long_term_cached_value('panhandler', 'current_build_time', build_date_string, 14400,
                                                     'app_update')
        except OSError as ose:
            print('Could not read build date data file')
            print(ose)
            return None

    print(build_date_string)
    return datetime.strptime(build_date_string, '%Y-%m-%dT%H:%M:%S')


def _get_current_tag() -> (str, None):
    tag_string = cnc_utils.get_long_term_cached_value('panhandler', 'current_tag')

    if not tag_string:
        print('Getting updated tag')
        panhandler_config = cnc_utils.get_app_config('panhandler')
        if 'app_dir' not in panhandler_config:
            return None

        tag_file = os.path.join(panhandler_config['app_dir'], 'tag')

        if not os.path.exists(tag_file) or not os.path.isfile(tag_file):
            return None

        try:
            with open(tag_file, 'r') as bf:
                tag_string = bf.read()
                cnc_utils.set_long_term_cached_value('panhandler', 'current_tag', tag_string, 14400, 'app_update')

        except OSError as ose:
            print('Could not read tag date data file')
            print(ose)
            return None

    return str(tag_string.strip())


def _get_panhandler_image_data():
    docker_hub_link = 'https://hub.docker.com/v2/repositories/paloaltonetworks/panhandler/tags/'
    try:
        # try to pull from cache is possible
        details_from_cache = cnc_utils.get_long_term_cached_value('panhandler', 'docker_image_details')
        if details_from_cache is not None:
            print('Returning docker_image_details from the cache')
            return details_from_cache

        print('Getting docker details from upstream')
        resp = requests.get(docker_hub_link, verify=False, timeout=5)
        if resp.status_code != 200:
            print('Could not fetch docker_image_details')
            print(resp.text)
            print(resp.status_code)
            return {}
        else:
            details = resp.json()
            cnc_utils.set_long_term_cached_value('panhandler', 'docker_image_details', details, 14400, 'app_update')
            return details
    except ConnectionError as ce:
        print('Could not contact docker hub API')
        print(ce)
        return {}
    except Timeout as te:
        print('Timed out waiting for docker image details')
        print(te)
        return {}
