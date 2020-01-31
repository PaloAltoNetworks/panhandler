.. _`example_terraform`:

.. _`jsonpath_ng`: https://github.com/h2non/jsonpath-ng#jsonpath-syntax

Example Terraform Skillet
=========================

This Skillet will launch a Terraform project. All user-inputs to the 'variables' section will be passed to terraform
as terraform variables. Therefore, the 'variable' names should match the terraform variable names exactly. Any
terraform 'outputs' will be automatically captured into the context for subsequent skillets to use.


.meta-cnc.yaml
--------------

.. code-block:: yaml

    name: azure_single_pavm

    label: Azure Single PAN-OS VM-Series

    description: Launch a single Single PAN-OS VM-Series in Azure.

    type: terraform

    labels:
      collection:
        - Example Skillets

    variables:
      - name: admin_username
        description: Admin Username
        default: panhandler
        type_hint: text
      - name: admin_password
        description: Admin Password
        default:
        type_hint: password
      - name: hostname
        description: Hostname
        default: panhandler-vm-01
        type_hint: text
      - name: resource_group
        description: Resource Group
        default: panhandler-unique-value-123
        type_hint: text



Terraform Variables
-------------------

In this case, our variables from the skillet definition file match the variables that terraform expects. Here is a
`variables.tf` file from this project:

.. code-block::

    variable "admin_username" {
      description = "PAN-OS NGFW Admin Username"
      default = "admin"
    }

    variable "admin_password" {
      description = "PAN-OS NGFW Admin Password"
      default = "admin"
    }

    variable "resource_group" {
      description = "Resource Group to use to build"
      default = "admin"
    }

    variable "hostname" {
      description = "Host name of the PA VM-Series"
      default = "pavm"
    }


Any user input from Panhandler will be passed to terraform as a TFVAR.


Terraform Output Capturing
--------------------------

All terraform 'outputs' are automatically captured into the context. Here is a sample 'outputs.tf' file:

.. code-block::

    data "azurerm_public_ip" "pavm_public_ip_address_data" {
      name                = "${azurerm_public_ip.pavm_public_ip.name}"
      resource_group_name = "${azurerm_virtual_machine.pavm.resource_group_name}"
    }

    output "pavm_public_ip_address" {
      value = "${data.azurerm_public_ip.pavm_public_ip_address_data.ip_address}"
    }

This will capture a variable named 'pavm_public_ip_address' in the Panhandler skillet context, where it can be used to
pre-populate input fields in other skillets, or passed to other skillets via `hidden` variables, etc.


Snippet Details
----------------

The 'snippets' section contains all the type specific configuration. Terraform does not require a 'snippet' section
as the skillet definition file is expected to live in the project root of the terraform project.