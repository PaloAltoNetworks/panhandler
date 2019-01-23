Panhandler Snippets
=============================

This directory holds all configured configuration snippets. Snippets represent multiple
bits of Pan-OS configuration, 3rd party device configurations, or other jinja templates that should be considered a
single entity. Often used to create 'services' or other related bits of configuration.

YAML syntax
-----------

Each 'Service' or 'Change' is structured as a series of files in a single directory. This directory contains
a number of snippet files (XML, YAML, JSON, etc) and a `.meta-cnc.yaml` file. Note the following:

1. A `.meta-cnc.yaml` file that is formatted with using YAML with the following format:

.. code-block:: yaml

    name: snippet_name
    description: snippet description
    extends: gsb_baseline
    target_version: 8.1+
    variables:
      - name: INF_NAME
        description: Interface Name
        default: Ethernet1/1
        type_hint: text
    snippets:
      - xpath: some/xpath/value/here
        name: snippet_knickname
        file: filename of xml snippet to load that should exist in this directory


2. Multiple configuration snippet files. Each should contain a valid template fragment and may use jinja2 variables.
 These templates may be XML, JSON, YAML, Text, etc. For Pan-OS devices, these are XML fragments from specific stanzas
 of the Pan-OS device configuration tree.


Snippet details
---------------

Each 'Service' or 'Change' .meta-cnc.yaml file must contain the following top-level keys:

    - name: name of this change
    - description: Short description of this change
    - extends: name of another change that is a dependency of this change
    - target_version: String referring to target version requirements. I.E This change applies only to Pan-OS 8.1
        or higher
    - variables: Described in detail below
    - snippets: a dict containing the following keys:
        - name: knickname of the snippet
        - file: filename of the snippet in the same directory
        - xpath (optional): XPath where this snippet belongs in the target OS heirarchy (for XML snippets)

Each snippet can define nulitple variables that will be interpolated using the Jinja2 templating language. Each
variable defined in the `variables` list should define the following:


1. name: The name of the variable found in the snippets. For example:

 .. code-block:: jinja

    {{ name }}


2. description: A brief description of the variable and it's purpose in the configuration
3. label: Human friendly label to display to user
4. extends: Name of another snippet to load
5. default: A valid default value which will be used if not value is provided by the user
6. type_hint: Used to constrain the types of values accepted. May be implemented by additional third party tools.
Examples are `text`, `ip_address`, `ip_address_with_subnet`, `number`, `enum`, 'password'


hints
-----

cd into a snippet dir and run this to find all vars

.. code-block:: bash

    grep -r '{{' . |  cut -d'{' -f3 | awk '{ print $1 }' | sort -u

