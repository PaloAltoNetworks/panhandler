Welcome to Panhandler!
======================

Panhandler is a lightweight utility used to aggregate and view or load configuration templates. The primary focus is
PAN-OS devices such as the NGFW or Panorama yet may be extended to other elements such as Terraform and 3rd party devices.

Using predefined templates helps fast-track the loading of well known or recommended configurations without extensive
searching and scrolling through GUI-click documentation. Each collection of configuration templates are known as `skillets`
that are either preloaded into panhandler at runtime or can be manually added as needed.


Skillets can be based on xml, json, text or any other config type used by each device. They are grouped by output action
including:

    + panos: load into a NGFW and commit

    + panorama: load into Panorama and commit

    + gpcs: load into Panorama with a push to GPCS

    + template: simple text render to the screen


To load a configuration into a device with panhandler, the user simply has to add the target information for the device
to be configured, select the skillet to load, enter the form data, and submit. Panhandler then captures the form data,
grabs each configuration element, and loads into the specified device.








