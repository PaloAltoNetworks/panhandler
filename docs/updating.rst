.. _Hub: https://cloud.docker.com/u/paloaltonetworks/repository/docker/paloaltonetworks/panhandler/general
.. _here: https://cloud.docker.com/u/paloaltonetworks/repository/docker/paloaltonetworks/panhandler/general

Keeping Up to Date
===================

As panhandler is a quickly evolving project with new features added frequently, it is advisable to ensure you update
to the latest periodically.


Ensuring you have the latest docker image
-----------------------------------------

Panhandler is primarily distributed as a docker image on Docker Hub_. To ensure you have the latest version, check
for new releases here_. To launch a newer version via docker:

.. code-block::

   docker run -p 80:80 paloaltonetworks/panhandler -d

This will create a container based on the latest image tag. Versioned panhandler images are also available and can be
found on Docker Hub.

.. Note::

    You must periodically pull new images from Docker hub to ensure you have the latest software with new features and
    bug fixes.


To ensure you have the most up to date software, perform a docker pull and specify the 'latest' tag.

.. code-block::

   docker pull paloaltonetworks/panhandler:latest
   docker run -p 80:80 paloaltonetworks/panhandler:latest -d


