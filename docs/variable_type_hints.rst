.. _Variables:

Variables
=========

Variables in a Skillet determine what a user can modify or customize before deployment. In Panhandler, these get
generated into a web form that a user can fill out. Each variable can have it's own 'type' determined by the 'type_hint'
attribute in the variable declaration. This page lists all the type hints for reference.

Variable Types:
^^^^^^^^^^^^^^^

* text

  Default input type for user input. Optional `allow_special_characters` if false will ensure only
  letters, digits, underscore, hyphens, and spaces are allowed in the input. Set to True to allow all special
  characters. Default is to allow special characters. Optional `attributes` allows forcing a minimum and/or
  maximum length of the entered value.

.. code-block:: yaml

  - name: FW_NAME
    description: Firewall hostname
    default: panos-01
    type_hint: text
    help_text: Hostname for this firewall.
    allow_special_characters: false
    attributes:
      min: 6
      max: 256


* password

  This type will mask user input by rendering a password type input box.

.. code-block:: yaml

  - name: user_password
    description: Firewall Password
    default:
    type_hint: password


* ip_address

  This type will ensure the entered value matches an IPv4 or IPv6 pattern without a subnet mask.

.. code-block:: yaml

  - name: ip_address
    description: IP Address
    default: 0.0.0.0
    type_hint: ip_address

* fqdn_or_ip

  This type will ensure the entered value matches an IPv4, IPv6, or a valid hostname pattern. This is the most
  flexible option for hostname, FQDNs, ip addresses or CIDRs.

.. code-block:: yaml

  - name: host
    description: Target Host
    default: 0.pool.ntp.org
    type_hint: fqdn_or_ip

* url

  This type will ensure the entered value matches a valid URL scheme.

.. code-block:: yaml

  - name: clone_url
    description: Git Repo Clone URL
    default: https://github.com/PaloAltoNetworks/Skillets.git
    type_hint: url

* cidr

  This type will ensure the entered value matches an IPv4 or IPv6 CIDR.

.. code-block:: yaml

  - name: ip_address
    description: IP Address
    default: 192.168.122.2/24
    type_hint: cidr

* email

  This type will ensure the entered value matches an email pattern.

.. code-block:: yaml

  - name: email
    description: Email
    default: support@noway.com
    type_hint: email
    help_text: Enter your email address here to receive lots of spam

* number

  This type will ensure the entered value is an integer. You may optionally supply the `min` and `max`
  attributes to ensure the entered value do not exceed or fall below those values.

.. code-block:: yaml

  - name: vlan_id
    description: VLAN ID
    default: 1001
    type_hint: number
    attributes:
      min: 1000
      max: 2000


* float

  This type will ensure the entered value is a float. You may optionally supply the `min` and `max`
  attributes to ensure the entered value do not exceed or fall below those values.

.. code-block:: yaml

  - name: price_per_mbps
    description: Price Per Mbps
    default: 1.50
    type_hint: float
    attributes:
      min: 1.00
      max: 500.00

* dropdown

  This type will render a `select` input control. This ensures the user can only select one of the options
  given in the `dd_list`.

.. code-block:: yaml

  - name: yes_no
    description: Yes No
    default: 'no'
    type_hint: dropdown
    dd_list:
      - key: 'Yes I do'
        value: 'yes'
      - key: 'No I dont'
        value: 'no'

.. note::

    The `default` parameter should match the `value` and not the `key`. The `key` is what will be shown to the user
    and the `value` is what will be used as the value of the variable identified by `name`.

.. warning::

    Some values such as `yes`, `no`, `true`, `false`, `on`, `off`, etc are treated differently in YAML. To ensure these values are
    not converted to a `boolean` type, ensure to put single quotes `'` around both the `key` and the `value` as in
    the example above. Refer to the YAML specification for more details: https://yaml.org/type/bool.html

* text_area

  This type renders a `TextArea` input control. This allows the user to enter multiple lines of input. The optional
  `attributes` attribute allows you to customize the size of the text area control.

.. code-block:: yaml

  - name: text_area
    description: Multi-Line Input
    default: |
      This is some very long input with lots of
      newlines and white    space
      and stuff. The optional attributes key can also be specified
      to control now the text_area is rendered in panhandler and other cnc apps.
    type_hint: text_area
    attributes:
      rows: 5
      cols: 10

* json

  This type renders a `TextArea` input control and ensures the input is properly formatted JSON data

.. code-block:: yaml

  - name: json_string
    description: JSON Input
    default: |
        {
            "key_test": "value_test",
            "key2_test": "value2_test",
        }
    type_hint: json

* disabled

  This type will show the default value in an input control, but the user cannot change it. This is useful to
  show values but not allow then to be changed.

.. code-block:: yaml

  - name: DISABLED
    description: No Bueno
    default: panos-01
    type_hint: disabled

* radio

  This type allows the user to select one option out of the `rad_list`.

.. code-block:: yaml

  - name: radio_box_example
    description: radios
    default: maybe
    type_hint: radio
    rad_list:
      - key: 'Yes'
        value: 'yes'
      - key: 'No'
        value: 'no'
      - key: 'Maybe'
        value: 'maybe'

* list

  This type will allow the user to input multiple entries. The values of the multiple
  entries will be converted to an appropriate type for the Skillet type being used. For
  python, the entries will be converted to a comma separated list. For Terraform, the
  values will be converted to a terraform appropriate string representation.

.. code-block:: yaml

  - name: list_input
    description: IP Subnets
    default: 10.10.10.1/24
    type_hint: list

* hidden

  This type will NOT show an input form control to the user, but the default value will be passed to the
  skillet. This is useful is you want to 'capture' an input from another skillet and pass it into the input
  of this skillet without having to include it in the input form.

.. code-block:: yaml

  - name: previous_value
    description: from previous skillet in workflow
    default: some_value
    type_hint: hidden
