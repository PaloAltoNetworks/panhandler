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
Palo Alto Networks panhandler

panhandler is a tool to find, download, and use Skillets

Please see http://panhandler.readthedocs.io for more information

This software is provided without support, warranty, or guarantee.
Use at your own risk.
"""

import pytest
import urllib3


@pytest.mark.scm
def test_with_authenticated_client(client, django_user_model):
    urllib3.disable_warnings()
    username = "paloalto"
    password = "panhandlertest"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)

    response = client.get('/panhandler/collections')
    assert response.status_code == 200

    response = client.get('/panhandler/repos')
    assert response.status_code == 200

    assert 'Import Skillet Repository' in response.content.decode('utf-8')

    response = client.get('/panhandler/import')
    assert response.status_code == 200

    assert 'Repository Name' in response.content.decode('utf-8')


@pytest.mark.scm
def test_repo_import(client, django_user_model):
    """
    Tests to perform the following actions:
        login
        import a repo
        verify skillet collection is found on repo details
        verify skillet label is found on repo details
        remove the repo
        verify skillet collection is NOT found in the collections page
        import a different repo with the same name
        verify different skillet collection is found
        verify different skillet label is found
        verify the skillet input form renders properly
        verify the skillet template renders with input variables
        remove the different repo

        Addresses issue GL #15
    """
    urllib3.disable_warnings()
    username = "paloalto"
    password = "panhandlertest"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)

    # Test to address issue #15
    response = client.get('/panhandler/repos')
    assert response.status_code == 200

    post_data = {
        'url': 'https://gitlab.com/panw-gse/as/panhandler_test.git',
        'repo_name': 'panhandler_test'
    }

    response = client.post('/panhandler/import', post_data, follow=True)
    assert response.status_code == 200
    assert 'Imported Repository Successfully' in response.content.decode('utf-8')

    response = client.get('/panhandler/repo_detail/panhandler_test')
    assert response.status_code == 200

    response_html = response.content.decode('utf-8')
    # Ensure the collection 'Test Skillets' is found in the repo details page output
    assert 'Test Skillets' in response_html

    # Ensure the skillet label is found in the repo details page output
    assert 'Template Example' in response_html

    # Now remove this repo
    response = client.get('/panhandler/remove_repo/panhandler_test', follow=True)
    assert response.status_code == 200

    assert 'Repo Successfully Removed' in response.content.decode('utf-8')

    # Ensure 'Test Skillets' collection is now gone
    response = client.get('/panhandler/collections')
    assert response.status_code == 200

    assert 'Test Skillets' not in response.content.decode('utf-8')

    # Import another repo with the same name
    response = client.get('/panhandler/repos')
    assert response.status_code == 200

    assert 'Import Skillet Repository' in response.content.decode('utf-8')

    response = client.get('/panhandler/import')
    assert response.status_code == 200

    assert 'Repository Name' in response.content.decode('utf-8')

    # Test to address issue #15 - New repo with the same name
    post_data = {
        'url': 'https://gitlab.com/panw-gse/as/panhandler_test_2.git',
        'repo_name': 'panhandler_test'
    }

    import_response = client.post('/panhandler/import', post_data, follow=True)
    assert import_response.status_code == 200
    assert 'Imported Repository Successfully' in import_response.content.decode('utf-8')

    detail_response = client.get('/panhandler/repo_detail/panhandler_test')
    assert detail_response.status_code == 200

    response_html = detail_response.content.decode('utf-8')
    assert 'Test Skillets' in response_html

    # Ensure the skillet label is found in the repo details page output
    assert 'Another Test Template' in response_html

    # Test Skillet rendering
    response = client.get('/panhandler/skillet/another_test')
    assert response.status_code == 200

    input_form_html = response.content.decode('utf-8')
    assert 'variable description' in input_form_html
    assert 'variable default' in input_form_html

    rendered_response = client.post('/panhandler/skillet/another_test', {
        'ANOTHER_VARIABLE': 'changed_value'
    })
    assert rendered_response.status_code == 200

    rendered_output = rendered_response.content.decode('utf-8')
    assert 'changed_value' in rendered_output

    # test skillet deletion
    # url requires repo_name / skillet_name
    del_response = client.get('/panhandler/delete_skillet/panhandler_test/another_test', follow=True)
    assert del_response.status_code == 200

    del_rendered_output = del_response.content.decode('utf-8')
    assert 'Skillet Deleted successfully' in del_rendered_output

    # Now remove this repo again
    response = client.get('/panhandler/remove_repo/panhandler_test', follow=True)
    assert response.status_code == 200

    response = client.get('/unlock_envs')
    assert response.status_code == 200

