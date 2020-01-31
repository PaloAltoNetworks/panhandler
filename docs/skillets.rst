Skillets
========

The heart of Panhandler is the `.meta-cnc.yaml` file. This allows a set of configuration snippets, known as a skillet,
to be shared and consumed as a single unit. For example, to configure a default security profile you may need to
configure multiple different parts of the PAN-OS configuration. Panhandler allows you to group those different 'pieces'
and share them among different devices as a single unit. Often times these configuration bits
(affectionately called 'skillets') need slight customization before deployment to a new device. The `.meta-cnc.yaml`
file provides a means to templatize these configurations and present a list of customization points, or variables,
to the end user or consumer.


IronSkillet
------------

The very first, and most well known, Skillet is `IronSkillet <https://github.com/PaloAltoNetworks/iron-skillet>`_. This
was developed as a way to share best practice Day One configurations in an easy to deploy manner without requiring
'a million clicks'.

Much more information about IronSkilet can be found on
`Readthedocs <https://iron-skillet.readthedocs.io/en/docs_master/>`_.


Basic concepts
--------------

In order to add multiple 'bits' of configuration to a device, we need to know the following things:

* XML Configuration fragment with optional variables defined in jinja2 format
* xpath where this xml fragment should be inserted into the candidate configuration
* the order in which these XML fragments must be inserted
* a list of all variables that require user input
* target version requirements. For example: PAN-OS 8.0 or higher

This is all accomplished by adding multiple files each containing an XML configuration fragment and a `.meta-cnc.yaml`
file that describes the load order, variables, target requirements, etc.


YAML syntax
-----------

Each `skillet` is structured as a series of files in a single directory. This directory may contain
a number of template files (XML, YAML, JSON, etc) and a `.meta-cnc.yaml` file. Note the following:

1. A `.meta-cnc.yaml` file that is formatted with using YAML with the following format:

.. code-block:: yaml

    name: config_set_id
    label: human readable text string
    description: human readable long form text describing this Skillet

    labels:
      collection:
        - Example Skillets

    variables:
      - name: INF_NAME
        description: Interface Name
        default: Ethernet1/1
        type_hint: text

    snippets:
      - xpath: some/xpath/value/here
        name: config_set_knickname
        file: filename of xml snippet to load that should exist in this directory



2. Multiple configuration files. Each should contain a valid template fragment and may use jinja2 variables.
   These templates may be XML, JSON, YAML, Text, etc. For PAN-OS devices, these are XML fragments from specific stanzas
   of the PAN-OS device configuration tree.


Metadata details
----------------

Each .meta-cnc.yaml file must contain the following top-level attributes:

* name: unique name of this Skillet
* label: Human readable label that will be displayed in the Panhandler UI
* description: Short description to give specific information about what this Skillet does
* type: The type of skillet. This can be 'panos', 'panorama', 'rest', or others.
* variables: Described in detail below
* snippets: a list od dicts. The required attributes vary according to Skillet tupe


Optional top level attributes:


* depends: List of dicts containing repository urls and branches that this skillet depends on
* labels: YAML dict of optional Skillet configuration information. For example - collection labels

.. note::

    Each Metadata file type has it's own format for the 'snippets' section. `file` and `xpath` are only used in
    `panos` and `panorama` types. Other types such as `template` or `rest` may have a different format.


Skillet Collections
^^^^^^^^^^^^^^^^^^^

Each Skillet should belong to at least one 'Collection'. Collections are used to group like skillets. SKillets
with no `collection` label will be placed in the 'Unknown' Collection.

To configure one or more collections for your Skillet, add a `collection` attribute to the 'labels' dictionary.

.. code-block:: yaml

    labels:
      collection:
        - Example Skillets
        - Another Collection
        - Yet another Collection



Snippet details per Metadata type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Required fields for each metadata type is listed below:

* panos, panorama, panorama-gpcs
    * name - name of this snippet
    * cmd - operation to perform. Default is 'set'. Any valid PAN-OS API Command is accepted (set, edit, override, get, show, etc)
    * xpath - XPath where this fragment belongs
    * file - path to the XML fragment to load and parse
    * element - inline XML fragment to load and parse. Can be used in leu of a separate 'file' field

    See Example here: :ref:`example_panos`

* pan_validation
    * name - name of the validation test to perform
    * cmd - validate, validate_xml, noop, or parse. Default is validate
    * test - Boolean test to perform using jinja expressions

    See Example here: :ref:`example_validation`

* template
    * name - name of this snippet
    * file - path to the jinja2 template to load and parse
    * template_title - Optional title to include in rendered output

* terraform
    * None - snippets are not used for terraform

    See Example here: :ref:`example_terraform`

* rest
    * name - unique name for this rest operation
    * path - REST URL path component `path: http://host/api/?type=keygen&user={{ username }}&password={{ password }}`
    * operation - type of REST operation (GET, POST, DELETE, etc)
    * payload - path to a jinja2 template to load and parse to be send as POSTed payload
        .. note:: For x-www-form-urlencded this must be a json dictionary
    * headers - a dict of key value pairs to add to the http headers
        .. note:: for example: `Content-Type: application/json`

    See Example here: :ref:`example_rest` and here: :ref:`example_rest_with_output`

* python3
    * name - name of the script to execute
    * file - relative path to the python script to execute
    * input_type - Optional type of input required for this script. Valid options are 'cli' or 'env'.
      This will determine how user input variables will be passed into
      into the script. The default is 'cli' and will pass variables as long form arguments to the script in the form
      of `--username=user_input` where `username` is the name of the variable defined in the `variables` section and
      `user_input` is the value entered for that variable from the user. The other option, 'env' use cause all
      defined variables to be set in the environment of the python process.

    See Example here: :ref:`example_python`

Defining Variables for User input
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each skillet can define multiple variables that will be interpolated using the Jinja2 templating language. Each
variable defined in the `variables` list should define the following:

1. name: The name of the variable found in the skillets. For example:

.. code-block:: jinja

    {{ name }}


2. description: A brief description of the variable and it's purpose in the configuration. This will be rendered as
   the field label in the UI.
3. default: A valid default value which will be used if no value is provided by the user.
4. type_hint: Used to constrain the types of values accepted. May be implemented by additional third party tools.
   Examples are `text`, `text_field`, `ip_address`, `password`, `dropdown`, and `checkbox`.
5. force_default: The UI will be pre-populated with a value from the loaded environment or with a previously
   entered value unless this value is set to True. The default is False. Setting to True will ensure the default
   value will always be rendered in the panhandler UI.
6. required: Determines if a value is required for this field. The default is False.
7. help_text: Optional attribute that will be displayed immediately under the field. This is useful for giving
   extra information to the user about the purpose of a field.

.. note::

    The variable name must not contain special characters such as '-' or '*' or spaces. Variable names can be any
    length and can consist of uppercase and lowercase letters ( A-Z , a-z ), digits ( 0-9 ), and the underscore
    character ( _ ). An additional restriction is that, although a variable name can contain digits, the first
    character of a variable name cannot be a digit.


Variable Examples:
^^^^^^^^^^^^^^^^^^

Here is an example variable declaration.

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


See :ref:`Variables` for a complete reference of all available type_hints.


Hints
-----

Ensuring all variables are defined
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When working with a large amount of configuration temlates, it's easy to miss a variable definition. Use this one-liner
to find them all.

cd into a skillet dir and run this to find all configured variables:

.. code-block:: bash

    grep -r '{{' . |  cut -d'{' -f3 | awk '{ print $1 }' | sort -u


Of, if you have `perl` available, the following may also catch any configuration commands that may have
more than one variable defined:

.. code-block:: bash

    grep -r '{{' . | perl -pne 'chomp(); s/.*?{{ (.*?) }}/$1\n/g;' | sort -u



YAML Syntax
^^^^^^^^^^^

YAML is notoriously finicky about whitespace and formatting. While it's a relatively simple structure and easy to learn,
it can often also be frustrating to work with, especially for large files. A good reference to use to check your
YAML syntax is the `YAML Lint site <http://www.yamllint.com/>`_.

Jinja Whitespace control
^^^^^^^^^^^^^^^^^^^^^^^^^^

Care must usually be taken to ensure no extra whitespace creeps into your templates due to Jinja looping
constructs or control characters. For example, consider the following fragment:

.. code-block:: jinja

    <dns-servers>
    {% for member in CLIENT_DNS_SUFFIX %}
        <member>{{ member }}</member>
    {% endfor %}
    </dns-servers>

This fragment will result in blank lines being inserted where the 'for' and 'endfor' control tags are placed. To
ensure this does not happen and to prevent any unintentioal whitespace, you can use jinja whitespace control like
so:

.. code-block:: jinja

    <dns-servers>
    {%- for member in CLIENT_DNS_SUFFIX %}
        <member>{{ member }}</member>
    {%- endfor %}
    </dns-servers>

.. note:: Note the '-' after the leading '{%'. This instructs jinja to remove these blank lines in the resulting
    parsed output template.


