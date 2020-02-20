Adding a New Skillet Repository
===============================

Panhandler is preloaded with a wide set of skillets yet you may still have to manually add skillet repos.

Import a New Skillet
--------------------

From the main menu, choose `Import Skillets`.

.. image:: images/ph-menu.png
    :width: 250


The import repository fields allow you to specify the repo name and URL to import. You may
import repositories from any git server, including GitHub, gitlab, gogs, etc.

To import a repository from Github, click on the 'Clone or Download' button and copy the full HTTPS link
shown.

.. image:: images/ph-github-clone-url.png


.. warning::

    Private Repositories and SSH based URLs are currently not supported


Also, note which branch you want to import. The list of available branches can be found in Github by clicking
the 'Branch: master' button on the main page of the repository.

.. image:: images/ph-github-branches.png


Enter this information in the 'Import Skillets' form to import the repository and gain access to the
Skillets contained within.


.. image:: images/ph-import-repo.png

Once successful, you will see the complete list of imported repositories including the newly added repo.

At this stage, going to the `Template Library` will show any additional skillets in their respective categories.


Update a Skillet Repository
---------------------------

From the main menu, choose `Repositories`.

.. image:: images/ph-menu.png
    :width: 250

Click on `Details` for the repository of interest.

.. image:: images/ph-repo-details-full.png

The repo window will show a description of the repo along with the last few content changes.

Choose `Update to Latest` to check for and pull template updates.

.. Note::
    `Already up to date` will show that no changes were made to the source skillet and no udpates required.


