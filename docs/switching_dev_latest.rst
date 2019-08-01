Switching between Latest and Develop Containers
===============================================

PanHandler runs in a Docker container, the main build tagged as 'latest'.

There is also a develop branch with new features and updates. Although not the recommended release, some users may
want to work with develop and explore new features. Some skillets being developed may also be dependent on newer features.


Updating the Running Latest Version
-----------------------------------

The following bash script can be copy-pasted into the terminal to stop the PanHandler process, pull the latest,
and run again. The example uses port 9999 for web access.

.. code-block:: bash

    export PANHANDLER_IMAGE=paloaltonetworks/panhandler
    export PANHANDLER_ID=$(docker ps | grep $PANHANDLER_IMAGE | awk '{ print $1 }')
    docker stop $PANHANDLER_ID
    docker rm -f $PANHANDLER_ID
    docker pull $PANHANDLER_IMAGE
    docker run -p 9999:80 -t -v $HOME:/root -d $PANHANDLER_IMAGE


Updating the Running Develop Version
------------------------------------

The following bash script can be copy-pasted into the terminal to stop the PanHandler process, pull the develop version,
and run again. The example uses port 9999 for web access.

.. code-block:: bash

    export PANHANDLER_IMAGE=paloaltonetworks/panhandler:dev
    export PANHANDLER_ID=$(docker ps | grep $PANHANDLER_IMAGE | awk '{ print $1 }')
    docker stop $PANHANDLER_ID
    docker rm -f $PANHANDLER_ID
    docker pull $PANHANDLER_IMAGE
    docker run -p 9999:80 -t -v $HOME:/root -d $PANHANDLER_IMAGE


Switching from Latest to Develop
--------------------------------

These commands still stop the latest main release version then pull down and run the latest develop version.
The latest release container will be deleted.

.. code-block:: bash

    export PANHANDLER_IMAGE_M=paloaltonetworks/panhandler
    export PANHANDLER_IMAGE_D=paloaltonetworks/panhandler:dev
    export PANHANDLER_ID=$(docker ps | grep $PANHANDLER_IMAGE_M | awk '{ print $1 }')
    docker stop $PANHANDLER_ID
    docker rm -f $PANHANDLER_ID
    docker pull $PANHANDLER_IMAGE_D
    docker run -p 9999:80 -t -v $HOME:/root -d $PANHANDLER_IMAGE_D


Switching from Develop to Latest
--------------------------------

These commands still stop the develop  version then pull down and run the latest main release version.
The develop version container will be deleted.

.. code-block:: bash

    export PANHANDLER_IMAGE_M=paloaltonetworks/panhandler
    export PANHANDLER_IMAGE_D=paloaltonetworks/panhandler:dev
    export PANHANDLER_ID=$(docker ps | grep $PANHANDLER_IMAGE_D | awk '{ print $1 }')
    docker stop $PANHANDLER_ID
    docker rm -f $PANHANDLER_ID
    docker pull $PANHANDLER_IMAGE_M
    docker run -p 9999:80 -t -v $HOME:/root -d $PANHANDLER_IMAGE_M


