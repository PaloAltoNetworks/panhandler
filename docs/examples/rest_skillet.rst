Example REST Skillet
====================

Here is a basic skillet of type 'rest'. This skillet will query the Palo Alto Networks Licensing API to track
usage of a given authcode. This skillet demonstrates several important aspects of the rest type.

.meta-cnc.yaml
--------------

.. code-block:: text

    name: track_license_usage
    # Label is what will appear in the panhandler UI
    label: Track PAN-OS License Usage

    description: |
      This skillet demonstrates a simple REST api call to track license usage for a given authcode

    # type of skillet (panos, panorama, panorama-gpcs, python3, rest, template, or terraform)
    type: rest

    # Labels allow grouping and type specific options and are generally only used in advanced cases
    # the collection label will determine to which skillet collection this belongs
    labels:
      collection: Rest Skillets

    # this example only requires two bits of information from the operator, the licensing api_key and the authcode
    # to check
    variables:
      - name: api_key
        description: Licensing API Key
        default: 0000-0000-0000-0000-0000
        type_hint: text
      - name: authcode
        description: Auth Code to Check
        default: ABC123
        type_hint: text

    # The snippets section is required and is a list of REST operators to perform
    snippets:
      - name: track
        path: https://api.paloaltonetworks.com/api/license/get
        operation: post
        payload: payload.j2
        headers:
          apiKey: '{{ api_key }}'
          Content-Type: application/x-www-form-urlencoded


Example Payload
---------------

Here are the contents of the payload.j2 file

.. code-block:: json

    {
    "authcode": "{{ authcode }}"
    }


Section Details
----------------

The 'snippets' section contains all the type specific configuration. Here are the details of each attribute:

* name - name of the rest operation. This will group any captured outputs later
* path - this is the full URL to query - You may include variables in this if desired
    * for example: path: `https://{{ host }}/api/query={{ query_value }}`
* operation - the REST type operation to perform, in this case we need to perform a POST
* payload - the relative path to a file to load and parse. If your headers include a 'Content-Type' and that type
  is 'application/x-www-form-urlencoded' or 'application/json' this file will be parsed using the 'json' library
  and passed to the 'requests.post' method as a 'data' attribute. In most cases, this file will be a simple
  json dictionary of key value pairs.
* headers - this is a dictionary of attributes that will be added to the HTTP headers for the request. Each 'value'
  of the key value pair will be variable interpolated. In this case, we need to pass the 'api_key' variable captured
  from the user.


