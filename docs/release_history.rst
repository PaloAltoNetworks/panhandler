.. _github: https://github.com/PaloAltoNetworks/Skillets
.. _inputs: https://github.com/PaloAltoNetworks/Skillets/blob/master/inputs/all_inputs/.meta-cnc.yaml

Release History
===============


V4.0
~~~~

* Released 9-2020

New Features:

* Skillet Editor
    A new UI to edit all aspects of a Skillet.

* Skillet Creation Tools
    This feature allows you to build a skillet from scratch in a number of different ways. For example, you
    can build a skillet from the differences between two saved configuration files.

* Improved Terraform Support
    Terraform now uses a docker image in the backend, which allows any arbitrary terraform version to be supported.
    This allows the skillet builder to choose customized docker image containing any version of terraform and
    supporting libraries.

* Support for SSH based git repositories
    This allows you to use private git repositories as well as push local changes back upstream.


V3.1
~~~~

* Released 3-2020

New Features:

* Support for docker type skillets
    This brings support for Ansible, Shell scripts, custom binaries, configurable Terraform versions, and more. See
    github_ for examples.


V3.0
~~~~

* Released 2-2020

New Features:

* New skillet type: pan_validation
    This allows PAN-OS configuration file analysis using a jinja language expressions. More example can be found on
    github_.
* Dynamic UI elements
    Allows variables to be shown or hidden based on the value of another variable.
* New variable types
    File uploads, Dynamic lists, new validations and `many more <https://github.com/PaloAltoNetworks/Skillets/blob/master/inputs/all_inputs/.meta-cnc.yaml>`_.


V2.2
~~~~

* Released 6-2019

New Features:

* Improved Input validation
* Python script support with configurable input types.
    Script arguments can be passed via cli arguments or as env variables
* Automatic update detection.
    Panhandler will check if you are running the latest and greatest version on startup
* PAN-OS Skillet debug support
    This allows you to verify what is going to be pushed to a PAN-OS device before actually pushing
* Skillet debug on import
    Checks all skillets during repository import for syntax errors
* Collections page now supports filtering and sorting


