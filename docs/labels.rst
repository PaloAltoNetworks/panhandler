.. _Labels:

Labels
======

Labels are key/value pairs attached to skillets. Labels are optional and allow adding additional parameters to Skillets
that may not be implemented by all Tools. Labels can be used for grouping, searching, sorting, and identifying skillets
beyond just a 'name' attribute. Labels can be used to extend Skillet functionality in arbitrary ways going forward. This
behaviour is very much influenced by BGPv4 labels and Kubernetes labels.


Panhandler Supported Labels
~~~~~~~~~~~~~~~~~~~~~~~~~~~


Panhandler recognizes the following labels:

* collection

  The `collection` label is used to group like Skillets. A skillet may belong to multiple collections. The collection
  label value is a list of collection to which the skillet belongs.

.. code-block:: yaml

    labels:
      collection:
        - Example Skillets
        - Test Skillets
        - Validation Skillets


* order

  Panhandler uses the 'order' label to sort the Skillets. Skillets without an 'order' label are sorted alphabetically
  by their 'label' attribute. Skillets with a lower 'order' tag will be display before those with a higher 'order' tag.

.. code-block:: yaml

    labels:
      order: 10


* help_link

  The `help_link` label can be used to display a link to additional documentation about a skillet. This will be shown
  in the 'Help' dialog from the '?' icon in the top right hand corner of the Skillet input form.

.. code-block:: yaml

    labels:
      help_link: https://panhandler.readthedocs.io/en/master/variables.html


* help_link_title

  The `help_link_title` will set the displayed title of the `help_link` in the Help dialog.

.. code-block:: yaml

    labels:
      help_link: https://panhandler.readthedocs.io/en/master/variables.html
      help_link_title: All available Variable Documentation

