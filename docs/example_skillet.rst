Example Skillet
---------------


In this example, we will create a skillet that allows the user to customize a single variable.


XML Fragment
=============

First, we'll extract the parts of the configuration that comprise this 'unit' of configuration changes (a skillet).
For example, this portion of the configuration describes the log-settings we would like to modify:

.. code-block:: xml

    <system>
        <match-list>
         <entry name="dhcp-log-match">
            <send-syslog>
                <member>mgmt-interface</member>
            </send-syslog>
            <filter>(eventid eq lease-start)</filter>
          </entry>
        </match-list>
    </system>
    <syslog>
        <entry name="mgmt-interface">
            <server>
                <entry name="mgmt-intf">
                    <transport>UDP</transport>
                    <port>514</port>
                    <format>BSD</format>
                    <server>{{ MGMT_IP }}</server>
                    <facility>LOG_USER</facility>
                </entry>
            </server>
        </entry>
    </syslog>


Notice here we have defined one variable: `MGMT_IP`. This will allow the user to insert their own management ip when
deploying.

.meta-cnc file
==============

.. code-block:: yaml

    name: example_log_setting
    label: Log Setting Example
    description: Example log setting to configure syslog
    type: panos
    extends:

    labels:
      service_type: userid

    variables:
      - name: MGMT_IP
        description: NGFW management IP address
        default: 192.168.0.1
        type_hint: ip_address

    snippets:
      - name: log_settings
        xpath: /config/shared/log-settings
        file: log_settings.xml


In this file, we give some basic information about what this skillet will do, what configuration bits will be applied,
and what variables the user can customize. Notice in the 'variables' section, we specify a variable entry with a 'name'
that matches the variable defined in the XML fragment. The 'snippets' section will inform Panhandler where in the
configuration this fragment should be inserted (xpath) and where to find the fragment (file).


Rendered Form
==============

This `.meta-cnc.yaml` will produce the following web form in Panhandler:

.. image:: images/ph-example-skillet.png

