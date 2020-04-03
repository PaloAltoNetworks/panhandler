.. _`example_panos_get`:

Example PAN-OS with Output Capturing
====================================

This is a very basic example showing how to 'get' a portion of the configuration and capture some returned data into
context variables. These variables are then accessible by subsequent skillets. A common practice is to
build a simple workflow where the first skillet 'gets' information from a device, then a template skillet
displays that data using a jinja rendered.


.meta-cnc.yaml
--------------


.. code-block:: yaml

    name: example-panos-cmd-get
    label: Example of how use the 'get' command for PAN-OS

    description: |
      This example Skillet shows how to retrieve information from a PAN-OS device using the 'get' command type. This example
      uses the 'get' command type to retrieve some data, then uses a couple of different capture types to parse out
      different bits from the returned data.

    type: panos
    labels:
      collection:
        - Example Skillets

    snippets:
      - name: system_object
        cmd: get
        xpath: /config/devices/entry[@name="localhost.localdomain"]/deviceconfig/system
        outputs:
          # You always need to specify what you want to capture from the returned data
          # Using 'capture_object' you can convert the returned XML data (default output_type for panos) into a
          # an object that we can manipulate with Jinja later if desired
          - name: results_as_object
            # the '.' capture pattern will convert the full output into an object
            capture_object: .
          # the 'capture_value' attribute will only pull out a specific part of the returned data into a variable.
          # This is good if you only need a smaller part of the returned data as a stand-alone variable
          - name: timezone
            capture_value: timezone
          # 'capture_object' will take an XPath query and construct an object based on the XML returned from the query
          - name: dns_servers_object
            capture_object: dns-setting
          # 'capture_value' also takes an XPath query, but will return the value from the xpath query
          - name: primary_dns_server
            capture_value: dns-setting/servers/primary

      - name: system_xml
        cmd: get
        xpath: /config/devices/entry[@name="localhost.localdomain"]/deviceconfig/system
        # If you would like to have the raw output from the cmd, you can set the 'output_type' to text. This will
        # create a variable in the context named 'results_as_str' with a value containing the full XML output
        # from the 'get' command
        output_type: text
        outputs:
          - name: results_as_str


