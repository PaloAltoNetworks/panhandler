.. _`example_terraform`:

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


Terraform State Files
---------------------

Terraform keeps its state in a special file on disk called the `terraform.tfstate` file. Panhandler
by default will store the terraform state in a file on the local filesystem in the same directory as the
skillet meta-data file. This allows you to destroy or refresh a previously deployed project from the
Panhandler GUI.

Deploying Multiple Projects with Panhandler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, terraform will only deploy exactly what is proscribed in the various terraform files. That
means that if you want to deploy two instances of the same project, you must 'trick' terraform into
thinking this is a new deployment and not a modification to a previous one. Panhandler allows you to do
this via the 'Override' option. When deploying a terraform project, if an existing `terraform.tfstate`
file is found, Panhandler will give you the option to 'override' the existing state. This will cause
Panhandler to backup the existing state and create a new state for this deployment.

.. warning::

    This is a potentially dangerous operation as Terraform can create many resources in your cloud
    environment that are only tied together via a state file. You must be sure you can destroy all the
    necessary resources before you continue with the 'override' option.




