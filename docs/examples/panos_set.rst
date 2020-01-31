.. _`example_panos`:

Example PAN-OS Skillet
======================

This is a very basic example showing how to 'set' a templatized portion of the configuration. The user will be
prompted two input values. Each one will be interpolated into the 'element' and 'set' into the NGFW configuration.


.meta-cnc.yaml
--------------


.. code-block:: yaml

    name: mySkillet
    label: Sets the Login Banner
    description: |
        Simple Skillet to demonstrate how to use the 'set' command type for panos skillets

    type: panos

    labels:
      collection:
        - Example Skillets

    variables:

      - name: hostname
        description: Firewall hostname
        default: next-gen-firewall-01
        type_hint: text

      - name: firewall_env
        description: Firewall Environment
        default: develop
        type_hint: dropdown
        dd_list:
          - key: Develop
            value: Develop
          - key: Production
            value: Production

    snippets:
      - name: login-banner-226180
        cmd: set
        xpath: /config/devices/entry[@name="localhost.localdomain"]/deviceconfig/system
        element: |-
            &lt;login-banner&gt; Be Aware {{ hostname }} is in {{ firewall_env }}. &lt;/login-banner&gt;



XML Payload
------------

PAN-OS Skillets that load smaller bits of XML configuration into the device, can contain those elements 'inline'
using the 'element' attribute. Larger chunks of XML can also be stored separately on the filesystem using the 'file'
attribute. The value of the 'file' attribute should be a relative path to the file to read and load. In both cases,
jinja variable interpolation is done before being sent to the NGFW.


Snippet Details
----------------

The 'snippets' section contains all the skillet type specific configuration. Here are the details of each attribute
for 'panos' type skillets:

* name - name of this snippet. Useful for debugging and determining which snippets were executed successfully.
* cmd - the command to execute. Valid options are
    - op - performs an xml encoded op command
        * Requires the 'cmd_str' attribute
    - set - performs a 'set'
        * Requires 'xpath' and either 'file' or 'element' attributes
    - edit  - performs an 'edit'
        * Requires 'xpath' and either 'file' or 'element' attributes
    - override - performs an 'override'
        * Requires 'xpath' and either 'file' or 'element' attributes
    - move - performs a 'move'
        * Requires the 'where' attribute
    - rename - performs a 'rename'
        * Requires the 'new_name' attribute
    - clone - performs a 'clone'
        * Requires the 'new_name' and 'xpath_from' attribute
    - delete - performs a 'delete'
        * Requires the 'xpath' attribute
    - show - performs a 'show'
        * Requires the 'xpath' attribute
    - get - performs a 'get'
        * Requires the 'xpath' attribute
    - cli - performs 'cli' command. ex: `show system info`
        * Requires the 'cmd_str' attribute
    - validate - performs a validate
        * Requires the 'test' attribute
    - validate_xml - validates an xml path with a loaded xml snippet
        * Requires 'xpath' and either 'file' or 'element' attributes
    - parse - parses a variable using output capturing
        * Requires 'variable' and 'outputs' attributes


