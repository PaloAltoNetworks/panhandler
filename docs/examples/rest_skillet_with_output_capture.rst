Example REST Skillet with Output Capturing
==========================================

Here is a basic skillet of type 'rest'. This skillet will query the Palo Alto Networks Licensing API to track
usage of a given authcode. This skillet demonstrates several important aspects of the rest type. This examle also
demonstrates how to parse the output and capture variables for re-use in another skillet.

.meta-cnc.yaml
--------------

.. code-block:: text

    name: generate_api_key
    label: Generate PAN-OS API Key
    type: rest

    description: |
      This skillet demonstrates a simple REST api call to a PAN-OS NGFW to generate a new API Key

    labels:
      collection: Rest Skillets

    variables:
      - name: TARGET_IP
        description: Host
        default: 127.0.0.1
        type_hint: fqdn_or_ip
      - name: TARGET_PORT
        description: Port
        default: 443
        type_hint: number
      - name: TARGET_USERNAME
        description: Username
        default: admin
        type_hint: text
      - name: TARGET_PASSWORD
        description: Password
        default: admin
        type_hint: password

    snippets:
      - name: key_gen
        path: https://{{ TARGET_IP }}:{{ TARGET_PORT }}/api/?type=keygen&user={{ TARGET_USERNAME }}&password={{ TARGET_PASSWORD }}
        # this should output capturing which will set a variable called 'api_key' in the workflow, which can be referenced
        # in a skillet called after this one, any variable with a name called api_key will be prepopulated with the
        # value that is captured from the output of this xml api command
        operation: get
        output_type: xml
        outputs:
          - name: api_key
            capture_pattern: result/key


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
  json dictionary of key value pairs. This is not required for an operation type of 'get'.
* headers - this is a dictionary of attributes that will be added to the HTTP headers for the request. Each 'value'
  of the key value pair will be variable interpolated. In this case, we need to pass the 'api_key' variable captured
  from the user. This is not used in this example,
* outputs_type: This is the type of structured data that will be returned from this operation. Valid options are 'xml',
  'json', and 'base64'.
* outputs: A list of dictionaries, each with the following format:
    - name: variable name that will be placed in the jinja context
    - capture_pattern: The xpath or jsonpath expression that will be evaluated. In this case, the xpath 'result/key'
        will return the text found at the XML Element found at this xpath.


Captured Outputs
-----------------

Any skillet that is called after this one will have the variable 'api_key' pre-populated with the value returned
from this skillet. This allows you to chain together skillets to gather information that can be used later anywhere
jinja variable interpolation is used.
