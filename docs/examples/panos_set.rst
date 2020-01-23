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



