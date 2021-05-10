.. Panhandler documentation master file, created by
    sphinx-quickstart on Wed Jan 30 09:51:50 2019.
    You can adapt this file completely to your liking, but it should at least
    contain the root `toctree` directive.

Panhandler
==========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   running
   using
   skillets
   example_skillet
   examples/example_skillets
   debugging


About
-----

Panhandler is a tool to manage and share PAN-OS configuration sets called `Skillets`.
A configuration set can be a full device configuration, or a set of configuration elements.
Panhandler allows you to import git repositories that contain
one or more of these configuration templates. Each template contains a set of configuration elements and variables that can
be customized for each deployment. Variables are presented in an auto-generated web form for an operator to complete.
Once complete, the template is rendered and pushed to a PAN-OS device.


Skillets allow an architect or builder to create a fully customizable configuration set with
the correct level of abstraction for their organization's needs. For example, the PAN-OS GUI
may offer 20 different options for a given feature, however, in your organization you may
want to standardize on 18 of those and allow customization of only 2 options. Skillets allow
you to do just that.


For more information about Skillets, see the
`Live community page <https://live.paloaltonetworks.com/t5/Skillets/ct-p/Skillets>`_.

For more information about building Skillets, see the
`Skillet Builder Documentation <https://skilletbuilder.readthedocs.io/en/latest/>`_.


Disclaimer
----------

This software is provided without support, warranty, or guarantee.
Use at your own risk.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
