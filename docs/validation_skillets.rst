PAN-OS Validation Skillets
--------------------------


PAN-OS Validation skillets are used to check the compliance of a PAN-OS device configuration. They are comprised
of a series of 'tests' that each check a specific portion of the configuration. Validation tests can be executed
in both 'online' as well as 'offline' mode.

Online mode will query the running configuration of a running NGFW via it's API.

Offline node will execute the tests against an uploaded configuration file. This is especially useful to checking
things like configuration backups, or devices where direct API access is not possible. 


.. _jinja: https://jinja.palletsprojects.com/en/2.10.x/templates/


Validation Tests
----------------

Each test is evaluated using jinja_ boolean expressions. This means each test can only result in a pass or fail. In
order to perform simple logical operations on the XML configuration, it must first be converted into variables that
can be passed to the jinja templating engine. Once the variables have been captured, we can test each one of them
with some logical operation.


Variable Capturing
~~~~~~~~~~~~~~~~~~

Panhandler will automatically inject the 'config' variable into the validation skillet
context to simplify capturing additional variables from it. The 'config' variable is the 'running'
configuration from the target device, or an uploaded configuration from the user. In either case, the 'config' variable
will always be present for validation skillets.

The following example shows variable capturing:

.. code-block:: yaml

    - name: parse config variable and capture outputs
        cmd: parse
        variable: config
        outputs:
          # create a variable named 'zone_names' which will be a list of the attribute 'names' from each zone
          # note the use of '//' in the capture_pattern to select all zones
          # the '@name' will return only the value of the attribute 'name' from each 'entry'
          - name: zone_names
            capture_pattern: /config/devices/entry/vsys/entry/zone//entry/@name
          # note here we can combine an advanced xpath query with 'capture_object'. This will capture
          # the full interface definition from the interface that contains the 'ip_to_find' value
          - name: interface_with_ip
            capture_object: /config/devices/entry/network/interface/ethernet//entry/layer3/ip/entry[@name="{{ ip_to_find }}"]/../..



This example captures two variables from the config: 'zone_names' and 'interface_with_ip'. The 'parse' cmd type informs
Panhandler that this step is going to pass the variable named in the 'variable' attribute to the output. The 'outputs'
attribute will then determine what specific parts of this variable we want to capture. The value of the 'outputs'
attribute is a list of dicts. Each dict represents one new variable that will be captured. The two options for
what you want to capture are 'capture_pattern' and 'capture_object'. Both types will query the 'config' variable
using an XPATH expression. The main difference is in how the results of that query are processed and returned.

Capture Pattern
~~~~~~~~~~~~~~~~

The 'capture_pattern' attribute will try to intelligently interpret the results of the XPATH query. This is most useful
as in the above when you would like to return a list of element attributes, or a list of element text values.

In the above example, the variable 'zone_names' will be a list with the following:

.. code-block:: python

    zone_name = [
      "trust",
      "untrust",
      "dmz"
    ]


Capture Object
~~~~~~~~~~~~~~

The 'capture_object' attribute will convert the returned XML into an dictionary object using the python 'xmltodict'
library. This is especially useful when you want to perform a large number of tests on the same basic part of the
config. This allows you to 'capture' one part of the config, then perform logic against lots of different parts of it.

In the example above, the variable 'interface_with_ip' will have the value:

.. code-block:: python

    interface_with_ip = {
      "layer3": {
        "ip": {
          "entry": {
            "@name": "10.10.10.10/24"
          }
        }
      }
    }



Validation Testing
~~~~~~~~~~~~~~~~~~

Once you have captured the various variables you want to test, use the 'validate' cmd type.


For example:

.. code-block:: yaml

    - name: zones_are_configured
      cmd: validate
      label: Ensure at least one zone is Configured
      test: zone_names is not none
      documentation_link: https://iron-skillet.readthedocs.io/en/docs_dev/viz_guide_panos.html#device-setup-management-general-settings


The 'test' attribute uses the jinja_ expression language to perform a boolean test on the supplied expression. In
this example, if zone_names is defined and has a value, then the test will pass.


A more complex example
~~~~~~~~~~~~~~~~~~~~~~

This example is slightly more complex and uses a number of features to accomplish this compliance check:

.. code-block:: yaml

      - name: device_config_file
        cmd: parse
        variable: config
        outputs:
          # capture all the xml elements under statistics-service for later evaluation
          - name: telemetry
            capture_object: /config/devices/entry[@name='localhost.localdomain']/deviceconfig/system/update-schedule/statistics-service

      - name: telemetry_fully_enabled
        label: enable all telemetry attributes
        test: |
          (
          telemetry | element_value('statistics-service.application-reports') == 'yes'
          and telemetry | element_value('statistics-service.threat-prevention-reports') == 'yes'
          and telemetry | element_value('statistics-service.threat-prevention-pcap') == 'yes'
          and telemetry | element_value('statistics-service.passive-dns-monitoring') == 'yes'
          and telemetry | element_value('statistics-service.url-reports') == 'yes'
          and telemetry | element_value('statistics-service.health-performance-reports') == 'yes'
          and telemetry | element_value('statistics-service.passive-dns-monitoring') == 'yes'
          and telemetry | element_value('statistics-service.file-identification-reports') == 'yes'
          )
        fail_message: telemetry should be enabled for all attributes
        documentation_link: https://iron-skillet.readthedocs.io/en/docs_dev/viz_guide_panos.html#device-setup-telemetry-telemetry


Here, we first capture the XML elements found under 'statistics-service' if any are found. This is then converted
into a variable object with the name 'telemetry'. The 'telemetry' object when fully configured will have the following
structure:

.. code-block:: python

    telemetry = {
      "statistics-service": {
        "application-reports": "yes",
        "threat-prevention-reports": "yes",
        "threat-prevention-pcap": "yes",
        "threat-prevention-information": "yes",
        "passive-dns-monitoring": "yes",
        "url-reports": "yes",
        "health-performance-reports": "yes",
        "file-identification-reports": "yes"
      }
    }


To facilitate a simple syntax to check this, custom jinja_ filters have been developed including 'element_value'. We
use 'element_value' here to return the value found at a specific 'path' inside the object. The 'path' is a '.' or '/'
separated list of attributes to check.

.. code-block:: yaml

    # this will evaluate to true in this case because the path 'statistics-service.application-reports' exists
    # and the value found therein is equal to the desired value of 'yes'
    telemetry | element_value('statistics-service.application-reports') == 'yes'


.. _`list of filters`: https://github.com/PaloAltoNetworks/skilletlib/blob/master/docs/jinja_filters.rst
.. _here: https://github.com/PaloAltoNetworks/skilletlib/blob/master/docs/jinja_filters.rst

For more information about all available custom filters and their example uses, see the `list of filters`_ documentation
here_.

PAN-OS Validation Examples
--------------------------

To get a sense of all that is possible, here are a couple of complete examples.

`CIS Benchmarks <https://gitlab.com/panw-gse/as/cis-benchmarks>`_ will validate a PAN-OS
device for `CIS <https://www.cisecurity.org/>`_ compliance.

`STIG Benchmarks <https://gitlab.com/panw-gse/as/stig_skillets>`_ will validate a PAN-OS device
for `STIG <https://public.cyber.mil/stigs/>`_ compliance.


Hints, Tips, Tricks
-------------------


Start with a Pass
~~~~~~~~~~~~~~~~~

Because you often need to know the structure of the configuration and the resulting objects, it is always a good idea
to start with a fully configured PAN-OS NGFW that will 'pass' the validation test you are writing.

.. _`Skillet Builder`: https://github.com/PaloAltoNetworks/skilletbuilder
.. _`example validation`: https://github.com/PaloAltoNetworks/skilletlib/tree/master/example_skillets

Use Tools to explore the config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also use the `Skillet Builder`_ tools found on github here: https://github.com/PaloAltoNetworks/skilletbuilder.
These are a set of Skillets designed to aid in building Skillets and especially Validation Skillets. Start with an
`example validation`_ skillet from here: https://github.com/PaloAltoNetworks/skilletlib/tree/master/example_skillets
and copy the contents in the 'Skillet Test Tool'. This will allow you to quickly test various capture patterns
and run different types of test quickly. It will also show you the structure of the XML snippets and objects returned
from your XPATH queries.