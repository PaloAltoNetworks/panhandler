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

.. code-block:: bash

   docker pull paloaltonetworks/panhandler:latest
   docker run -p 80:80 -t -v $HOME:/root paloaltonetworks/panhandler

This will create a container based on the latest image tag. Versioned panhandler images are also available and can be
found on Docker Hub.

.. Note::

    You must periodically pull new images from Docker hub to ensure you have the latest software with new features and
    bug fixes.


To ensure you have the most up to date software, perform a docker pull and specify your desired release tag.

.. code-block:: bash

   export TAG=latest
   docker pull paloaltonetworks/panhandler:$TAG
   docker run -p 80:80 -t -v $HOME:/root paloaltonetworks/panhandler:$TAG


Ensuring your Panhandler container is using the latest image
------------------------------------------------------------

If you already have Panhandler running, you may need to use the following commands to first stop the existing
container. Note the image tag in the PANHANDLER_IMAGE variable below. You may want to change this to 'latest'
or some other specific release tag like '2.2'

.. code-block:: bash

    export PANHANDLER_IMAGE=paloaltonetworks/panhandler:dev
    export PANHANDLER_ID=$(docker ps | grep $PANHANDLER_IMAGE | awk '{ print $1 }')
    docker stop $PANHANDLER_ID
    docker rm -f $PANHANDLER_ID
    docker pull $PANHANDLER_IMAGE
    docker run -p 80:80 -t -v $HOME:/root -d $PANHANDLER_IMAGE

