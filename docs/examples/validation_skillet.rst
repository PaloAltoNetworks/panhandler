Example Validation Skillet
==========================

This is a very basic example showing validate a portion of a PAN-OS configuration. Often times, you need to check
for specific values or apply some simple logic to a portion of the config to determine if it is considered
compliant or not. Skillets of type `pan_validation` allow you to do just that.

By default, Panhandler will always supply a variable called 'config' that contains the NGFW running config. The `parse`
cmd can be used to pull out and capture specific parts of that config. In this example, we use an advanced `xpath` query
to return a variable containing a list of all zone names configured in the running config. Another advanced `xpath` is
also used to find an ethernet interface with a specific IP Address. That interface is converted to an object using
`capture_object`.

The snippets with a cmd type of `validate` is where the actual compliance checks are performed. The `test` attribute
will be evaluated as a jinja boolean expression. True values are considered to have 'passed' this test.


.meta-cnc.yaml
--------------


.. code-block:: yaml

    #
    # Example Validation Skillet
    #
    name: example-validate-with-xpath-capture
    label: Example of how to use xpath queries to capture specific items of interest.

    description: |
      This example Skillet shows how to parse and validate a config using xpath syntax. This example checks the
      configured zones to ensure we do not have one with the attribute name equal to 'does-not-exist'

    type: pan_validation
    labels:
      collection:
        - Example Skillets
        - Validation

    variables:
      # this will allow the user to input a zone name to test
      - name: zone_to_test
        description: Name of the Zone to test for absence
        default: does-not-exist
        type_hint: text
      # as well as an IP address to search for as well
      - name: ip_to_find
        description: IP Address to locate
        default: 10.10.10.10/24
        type_hint: ip_address

    snippets:
      - name: parse config variable and capture outputs
        cmd: parse
        variable: config
        outputs:
          # create a variable named 'zone_names' which will be a list of the attribute 'names' from each zone
          # note the use of '//' to select all zones
          # the '@name' will return only the value of the attribute 'name' from each 'entry'
          - name: zone_names
            capture_pattern: /config/devices/entry/vsys/entry/zone//entry/@name
          # note here we can combine an advanced xpath query with 'capture_object'. This will capture
          # the full interface definition from the interface that contains the 'ip_to_find' value
          - name: interface_with_ip
            capture_object: /config/devices/entry/network/interface/ethernet//entry/layer3/ip/entry[@name="{{ ip_to_find }}"]/../..

      # simple test using a jinja expression to verify the 'zone_to_test' variable is not in the 'zone_names' test
      - name: ensure_desired_zone_absent_from_list
        # pan_validation skillet have a default cmd of 'validate'
        cmd: validate
        # note here that you can use jinja variable interpolation just about anywhere
        label: Ensures the {{ zone_to_test }} zone is not configured
        test: zone_test_test not in zone_names
        fail_message: |
          This fail message contains a variable, which is useful for debugging and testing.
          captured values were: {{ zone_names | tojson() }} and {{ interface_with_ip | default('none')| tojson() }}
        # documentation link helps give the user some context about why this test failed or how to manually remediate
        documentation_link: https://github.com/PaloAltoNetworks/skilletlib/blob/develop/docs/source/examples.rst




