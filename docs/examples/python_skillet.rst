.. _`example_python`:

Example Python Skillet
======================

This Skillet will launch a python script and capture variables from it's output. This python script requires it's
input form the user to be included in the OS Environment rather than on the CLI, so the 'input_type' attribute has
been set to 'env' rather than the default 'cli'.

.. _`jsonpath_ng`: https://github.com/h2non/jsonpath-ng#jsonpath-syntax

This script also returns JSON encoded structured data. We can use `jsonpath_ng`_ expressions to query and capture
specific variables from the output. For more inforation on JSON Path expression, see the `jsonpath_ng`_ library.


.meta-cnc.yaml
--------------

.. code-block:: yaml

    name: python3_env_input_example

    label: Example Python Script Argument Parsing

    description: |
      This skillet demonstrates a simple Python script in action with Env based input arguments and list handling.

    type: python3

    labels:
      collection:
        - Example Skillets

    variables:
      - name: USERNAME
        description: Username
        default: admin
        type_hint: text
      - name: PASSWORD
        description: Password
        default:
        type_hint: password

    snippets:
      - name: script
        file: input_from_env.py
        input_type: env
        output_type: json
        outputs:
          - name: captured_username
            capture_pattern: 'output_example.captured_username'
          - name: captured_secret
            capture_pattern: 'output_example.captured_secret'



Snippet Details
----------------

The 'snippets' section contains all the skillet type specific configuration. Here are the details of each attribute
for 'python3' type skillets:

* name - name of this snippet. Useful for debugging and determining which snippets were executed successfully.

* file - relative path to the Python script to execute
    * for example: file: `../run_reticulating_splines.py`

* input_type - how input variables from the user will be passed to the script. Valid options are:
    - env - All variables from the 'variables' section will be set in the OS Environment
    - cli - All variables will be passed in via long form command line arguments
        * for example `$: ./run_reticulating_splines.py --some_argument="my-hostname" --another_var="123"`

