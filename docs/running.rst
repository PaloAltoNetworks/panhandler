Running PanHandler
==================


The easiest way to run panhandler is to pull the docker container:

docker run -p 80:80 nembery/panhandler

Then access the UI via http://localhost:80

The default username and password is: `pan` and `panhandler`


Building PanHandler
-------------------

If you want to build panhandler from source (which is not recommended). You will need to update the git submodules,
install the pip python requirements for both the app and also CNC, create the local db, and create a local user.

.. code-block::
    git submodule init
    git submodule update
    pip install -r requirements.txt
    pip install -r cnc/requirements.txt
    ./cnc/manage.py migrate
    ./cnc/manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('pan', 'admin@example.com', 'panhandler')"


