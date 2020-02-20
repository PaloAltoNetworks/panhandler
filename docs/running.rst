Running Panhandler
==================

The recommended way to run Panhandler is to pull and run the docker container.


Quickstart
----------

The following command will ensure you have the most up to date version of panhandler and will set
up all the required ports and volume mounts. This command will also update existing Panhandler containers
with the latest released version.

.. code-block:: bash

    curl -s -k -L http://bit.ly/2xui5gM | bash


This command will install and or update Panhandler to the latest version using the default values.

If you need special requirements, such as custom volume mounts, non-default username and password, or
non-standard ports, you set the following environment variables prior to launching the 'curl' command:

* CNC_USERNAME - Set the default username to login to the application (default paloalto)
* CNC_PASSWORD - Set the default password to login to the application (default panhandler)
* IMAGE_TAG - Set the tag you want to download and install. Possible values: (dev, latest) (default latest)
* DEFAULT_PORT - Set the port the application will listen on for web requests (default 8080)
* FORCE_DEFAULT_PORT- Ensure your desired port will be used regardless of any previously set ports. Possible values are 'true' or 'false'


.. note::

    You must set 'FORCE_DEFAULT_PORT' to 'false' if you change the 'DEFAULT_PORT' to some value other than what was
    previously set!

Running the Panhandler Docker Container
---------------------------------------

If you need to manage the Panhandler container manually for some reason, following these steps:

Using a standard web port
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    docker run -t -p 8080:8080 -v ~:/home/cnc_user paloaltonetworks/panhandler

Then access the UI via http://localhost:8080

The default username and password is: `paloalto` and `panhandler`


Setting the Default Username and Password
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To set the default username and password, pass in the following environment variables:

.. code-block:: bash

   docker run -t -e CNC_USERNAME=myuser -e CNC_PASSWORD=mypass -p 80:8080 -v ~:/home/cnc_user paloaltonetworks/panhandler



Using an alternate TCP port
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If port 80 is unavailable, you can switch to a different port. This example uses port 9999.

.. code-block:: bash

    docker run -t -p 9999:8080 -v ~:/home/cnc_user paloaltonetworks/panhandler

Then access the UI via http://localhost:9999

To persist any environments and secrets, you can mount a volume on the `/home/cnc_user` folder like this:

.. code-block:: bash

    docker run -t -p 9999:8080 -v ~:/home/cnc_user paloaltonetworks/panhandler

.. Note::
    The -t option for `terminal` allows you to view panhandler output data in the terminal window.
    This is useful for determining any skillets errors that write to terminal output.


Stopping the docker container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The docker container runs in the background. You can stop the container by using its container ID.

.. code-block:: bash

    docker ps
    docker stop { CONTAINER ID }


.. image:: images/ph-docker-stop.png
    :width: 500


.. Note::
    If you need to remove the container, enter `docker rm { CONTAINER ID }` with CONTAINER ID as the
    ID used to stop. You must stop the container before deleting.



Building Panhandler
-------------------

If you want to build panhandler from source (which is not recommended). You will need to update the git submodules,
install the pip python requirements for both the app and also CNC, create the local db, and create a local user.

.. code-block:: bash

    git clone https://github.com/PaloAltoNetworks/panhandler.git
    cd panhandler
    git submodule init
    git submodule update
    pip install -r requirements.txt
    ./cnc/manage.py migrate
    ./cnc/manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('paloalto', 'admin@example.com', 'panhandler')"


Running Panhandler manually
---------------------------

To start the application on your local machine on port 80:

.. code-block:: bash

    cd panhandler/cnc
    celery -A pan_cnc worker --loglevel=info &
    manage.py runserver 80

To use a different port, supply a different argument to the runserver command above. In this case, the server will
start up on port 80. Browse to http://localhost in a web browser to begin. The default login credentials are 'paloalto'
and 'panhandler'


Requirements
------------

Panhandler has been tested to work on Docker version: 18.09.1 (Mac) and 18.09.0 (Linux).
Please ensure you have the latest docker version installed for the best results.

