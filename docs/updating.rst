.. _Hub: https://cloud.docker.com/u/paloaltonetworks/repository/docker/paloaltonetworks/panhandler/general
.. _here: https://cloud.docker.com/u/paloaltonetworks/repository/docker/paloaltonetworks/panhandler/general

Keeping Up to Date
===================

As panhandler is a quickly evolving project with new features added frequently, it is advisable to ensure you update
to the latest periodically.


Update Script
-------------

The following script is useful to update your version of Panhandler to the latest while retaining all your settings,
port mappings, etc.

.. code-block:: bash

    curl -s -k -L http://bit.ly/2xui5gM | bash


This script will pull down a bash script that will determine if your version of Panhandler is the latest. If not,
it will pull the latest image from Docker Hub_, remove the old container and create a new container with the same
port mapping as the previous version.

.. note::

    If you are upgrading from a very old Panhandler version, you may need to import Skillet repositories again.


Manually updating the Panhandler Container
-------------------------------------------

Panhandler is primarily distributed as a docker image on Docker Hub_. To ensure you have the latest version, check
for new releases here_. To manually launch a newer version via docker:

.. code-block:: bash

   docker pull paloaltonetworks/panhandler:latest
   docker run -p 8080:8080 -t -v $HOME:/home/cnc_user paloaltonetworks/panhandler

This will create a container based on the latest image tag. Versioned panhandler images are also available and can be
found on Docker Hub.

.. Note::

    You must periodically pull new images from Docker hub to ensure you have the latest software with new features and
    bug fixes.


To ensure you have the most up to date software, perform a docker pull and specify your desired release tag.

.. code-block:: bash

   export TAG=latest
   docker pull paloaltonetworks/panhandler:$TAG
   docker run -p 8080:8080 -t -v $HOME:/home/cnc_user paloaltonetworks/panhandler:$TAG


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
    docker run -p 8080:8080 -t -v $HOME:/home/cnc_user -d $PANHANDLER_IMAGE


Cleaning up old versions
------------------------

Once you update to a newer version of Panhandler, the older images can still be left around, taking up space on your
hard drive. A common best practice is to occasionally remove old images with the following docker command:

.. code-block:: bash

    docker image prune

.. note::

    This command may take some time to complete, up to several minutes. The longer it takes, the more space
    it's saving on your hard drive!


On my system, this command can regularly reclaim over 10GB of space.

Another good command to occasionally run is:

.. code-block:: bash

    docker container prune

This will remove all stopped containers and recover their used disk space as well.