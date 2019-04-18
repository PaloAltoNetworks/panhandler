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
   importing_skillets
   metadata_configuration
   example_skillet
   environments
   updating
   examples/rest_skillet


About
-----

Panhandler is a tool to manage and share PAN-OS configuration sets. A configuration set can be a full device
configuration, or a set of configuration elements. Panhandler allows you to import git repositories that contain
one or more configuration templates. Each template contains a set of configuration elements and variables that can
be customized for each deployment. Variables are presented in an auto-generated web form for an operator to complete.
Once complete, the template is rendered and pushed to a PAN-OS device.




Disclaimer
----------

This software is provided without support, warranty, or guarantee.
Use at your own risk.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
