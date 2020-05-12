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

panhandler is a tool to find, download, and use PAN-OS Skillets

Please see http://panhandler.readthedocs.io for more information

This software is provided without support, warranty, or guarantee.
Use at your own risk.
"""

import json
import os
from collections import OrderedDict
from datetime import datetime

import oyaml
import requests
from django.core.exceptions import ObjectDoesNotExist
from requests import ConnectionError
from requests import Timeout
from skilletlib import SkilletLoader

from pan_cnc.lib import cnc_utils
from ..models import RepositoryDetails
from ..models import Skillet


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
                    # account for build time and time to upload to docker hub
                    if delta.total_seconds() > 600:
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
        print('Getting updated build_date_string')
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


def initialize_repo(repo_detail: dict) -> list:
    """
    Initialize a git repository object using the supplied repositories details dictionary object
    :param repo_detail:
    :return: list of Skillets found in that repository
    """
    repo_name = repo_detail.get('name', '')
    (repository_object, created) = RepositoryDetails.objects.using('panhandler').get_or_create(
        name=repo_name,
        defaults={'url': repo_detail.get('url', ''),
                  'details_json': json.dumps(repo_detail)
                  }
    )

    if created:
        print(f'Indexing new repository object: {repository_object.name}')
        return refresh_skillets_from_repo(repo_name)

    return load_skillets_from_repo(repo_name)


def load_skillets_from_repo(repo_name: str) -> list:
    """
    returns a list of skillets from the repository as found in the db
    :param repo_name: name of the repository to search
    :return: list of skillet dictionary objects
    """
    all_skillets = list()

    try:
        repo_object = RepositoryDetails.objects.using('panhandler').get(name=repo_name)

        repo_skillet_qs = repo_object.skillet_set.all()
        for skillet in repo_skillet_qs:
            all_skillets.append(json.loads(skillet.skillet_json))

        return all_skillets

    except ObjectDoesNotExist:
        return all_skillets
    except ValueError:
        return all_skillets


def load_all_skillets(refresh=False) -> list:
    """
    Returns a list of skillet dictionaries
    :param refresh: Boolean flag whether to use the cache or force a cache refresh
    :return: skillet dictionaries
    """
    if refresh is False:
        cached_skillets = cnc_utils.get_long_term_cached_value('panhandler', 'all_snippets')
        if cached_skillets is not None:
            return cached_skillets

    skillet_dicts = list()
    skillets = Skillet.objects.using('panhandler').all()
    for skillet in skillets:
        skillet_dicts.append(json.loads(skillet.skillet_json))

    cnc_utils.set_long_term_cached_value('panhandler', 'all_snippets', skillet_dicts, -1)
    return skillet_dicts


def load_skillets_with_label(label_name, label_value):
    filtered_skillets = list()
    all_skillets = load_all_skillets()

    for skillet in all_skillets:
        if 'labels' in skillet and label_name in skillet['labels']:
            if type(skillet['labels'][label_name]) is str:

                if skillet['labels'][label_name] == label_value:
                    filtered_skillets.append(skillet)

            elif type(skillet['labels'][label_name]) is list:
                for label_list_value in skillet['labels'][label_name]:
                    if label_list_value == label_value:
                        filtered_skillets.append(skillet)

    return filtered_skillets


def load_all_skillet_label_values(label_name):
    labels_list = list()
    skillets = load_all_skillets()
    for skillet in skillets:
        if 'labels' not in skillet:
            continue

        labels = skillet.get('labels', [])

        for label_key in labels:
            if label_key == label_name:

                if type(labels[label_name]) is str:
                    label_value = labels[label_name]
                    if label_value not in labels_list:
                        labels_list.append(label_value)

                elif type(labels[label_name]) is list:
                    for label_list_value in labels[label_name]:
                        if label_list_value not in labels_list:
                            labels_list.append(label_list_value)

    return labels_list


def refresh_skillets_from_repo(repo_name: str) -> list:
    all_skillets = list()

    user_dir = os.path.expanduser('~/.pan_cnc')
    snippets_dir = os.path.join(user_dir, 'panhandler/repositories')
    repo_dir = os.path.join(snippets_dir, repo_name)

    try:
        repo_object = RepositoryDetails.objects.using('panhandler').get(name=repo_name)

        sl = SkilletLoader()

        found_skillets = sl.load_all_skillets_from_dir(repo_dir)

        for skillet_object in found_skillets:
            skillet_name = skillet_object.name
            (skillet_record, created) = Skillet.objects.using('panhandler').get_or_create(
                name=skillet_name,
                defaults={
                    'skillet_json': json.dumps(skillet_object.skillet_dict),
                    'repository_id': repo_object.id,
                }
            )

            if not created:
                # check if skillet contents have been updated
                found_skillet_json = json.dumps(skillet_object.skillet_dict)
                if skillet_record.skillet_json != found_skillet_json:
                    skillet_record.skillet_json = found_skillet_json
                    skillet_record.save()

        for db_skillet in repo_object.skillet_set.all():
            found = False
            for found_skillet in found_skillets:
                if db_skillet.name == found_skillet.name:
                    found = True
                    continue

            if not found:
                db_skillet.remove()

        update_skillet_cache()

        return load_skillets_from_repo(repo_name)

    except ObjectDoesNotExist:
        return all_skillets


def load_skillet_by_name(skillet_name: str) -> (dict, None):
    try:
        skillet = Skillet.objects.using('panhandler').get(name=skillet_name)
        return json.loads(skillet.skillet_json)
    except ObjectDoesNotExist:
        return None
    except ValueError as ve:
        print(f'Could not parse Skillet metadata in load_skillet_by_name')
        return None


def update_skillet_cache() -> None:
    """
    Updates the 'all_snippets' key in the cnc cache. This gets called whenever a repository is initialized or updated
    to ensure the legacy cache is always kept up to date
    :return: None
    """
    all_skillets = load_all_skillets(refresh=True)
    cnc_utils.set_long_term_cached_value('panhandler', 'all_snippets', all_skillets, -1)


def get_repository_details(repository_name: str) -> (dict, None):
    """
    returns the details dict as loaded from the database record for this db
    :param repository_name: name of the repository to find and return
    :return: loaded dict or None if not found
    """

    if RepositoryDetails.objects.using('panhandler').filter(name=repository_name).exists():
        try:
            repo_db_record = RepositoryDetails.objects.using('panhandler').get(repository_name)
            return json.loads(repo_db_record.details_json)
        except ValueError as ve:
            print(ve)
            return None
    else:
        return None
