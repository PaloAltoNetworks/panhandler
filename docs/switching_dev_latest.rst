Switching between Latest and Develop Containers
-----------------------------------------------

PanHandler runs in a Docker container, the main build tagged as 'latest'.

There is also a develop branch with new features and updates. Although not the recommended release, some users may
want to work with develop and explore new features. Some skillets being developed may also be dependent on newer features.


Updating the Running Latest Version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script will install or update to the latest 'dev' image for Panhandler. This is recommended for developers
or power-users who understand this code may be unstable and not all features may work all the time.

.. code-block:: bash

    curl -s -k -L http://bit.ly/34kXVEn  | bash


The following bash script can be copy-pasted into the terminal to stop the PanHandler process, pull the latest,
and run again. The example uses port 9999 for web access.

.. code-block:: bash

    export PANHANDLER_IMAGE=paloaltonetworks/panhandler
    export PANHANDLER_ID=$(docker ps | grep $PANHANDLER_IMAGE | awk '{ print $1 }')
    docker stop $PANHANDLER_ID
    docker rm -f $PANHANDLER_ID
    docker pull $PANHANDLER_IMAGE
    docker run -t -p 9999:80 -t -v $HOME/.pan_cnc:/home/cnc_user/.pan_cnc $PANHANDLER_IMAGE


Updating the Running Develop Version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following bash script can be copy-pasted into the terminal to stop the PanHandler process, pull the develop version,
and run again. The example uses port 9999 for web access.

.. code-block:: bash

    export PANHANDLER_IMAGE=paloaltonetworks/panhandler:dev
    export PANHANDLER_ID=$(docker ps | grep $PANHANDLER_IMAGE | awk '{ print $1 }')
    docker stop $PANHANDLER_ID
    docker rm -f $PANHANDLER_ID
    docker pull $PANHANDLER_IMAGE
    docker run -t -p 9999:80 -t -v $HOME/.pan_cnc:/home/cnc_user/.pan_cnc $PANHANDLER_IMAGE_D


Switching from Latest to Develop
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These commands still stop the latest main release version then pull down and run the latest develop version.
The latest release container will be deleted.

.. code-block:: bash

    export PANHANDLER_IMAGE_M=paloaltonetworks/panhandler
    export PANHANDLER_IMAGE_D=paloaltonetworks/panhandler:dev
    export PANHANDLER_ID=$(docker ps | grep $PANHANDLER_IMAGE_M | awk '{ print $1 }')
    docker stop $PANHANDLER_ID
    docker rm -f $PANHANDLER_ID
    docker pull $PANHANDLER_IMAGE_D
    docker run -t -p 9999:80 -t -v $HOME/.pan_cnc:/home/cnc_user/.pan_cnc $PANHANDLER_IMAGE_D


Switching from Develop to Latest
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These commands still stop the develop  version then pull down and run the latest main release version.
The develop version container will be deleted.

.. code-block:: bash

    export PANHANDLER_IMAGE_M=paloaltonetworks/panhandler
    export PANHANDLER_IMAGE_D=paloaltonetworks/panhandler:dev
    export PANHANDLER_ID=$(docker ps | grep $PANHANDLER_IMAGE_D | awk '{ print $1 }')
    docker stop $PANHANDLER_ID
    docker rm -f $PANHANDLER_ID
    docker pull $PANHANDLER_IMAGE_M
    docker run -t -p 9999:80 -t -v $HOME/.pan_cnc:/home/cnc_user/.pan_cnc $PANHANDLER_IMAGE_M


When switching between dev and latest clear the cache with the following link:

http://localhost:9999/clear_cache