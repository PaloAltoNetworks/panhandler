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


def test_placeholder():
    assert True

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

    response = client.get('/unlock_envs')
    assert response.status_code == 200
