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
   docker run -p 80:80 paloaltonetworks/panhandler:v1.0.2 -d

This will create a container based on the 1.0.2 image version. Panhandler also uses the 'latest' tag as well, which is
always kept up to date with the latest version. To ensure you are using the most up to date image with the latest tag,
issue these commands

.. code-block::
   docker pull paloaltonetworks/panhandler:latest
   docker run -p 80:80 paloaltonetworks/panhandler:latest -d


