When things go wrong
====================

Sometimes you may hit bugs or other unexpected behaviours. This page should give you some information
about how to recover your environment in the event something goes sideways.


Restarting the docker container
--------------------------------

Some types of problems can be fixed by restarting the container

.. code::

    # get the docker ID of the panhandler container
    docker ps | grep panhandler

    # use the 12 digit ID in the restart command
    docker restart 3fd4e2c78557

    # or as a one-linter
    docker ps | grep panhandler | awk '{ print $1 }' | xargs -n 1 docker restart



Clearing the cache
------------------

If you are seeing inconsistent data in the UI after a failed git import or some other error condition,
this can indicate the cache is out of date. Since the cache survives a docker restart, you may need to manually
perform a clear. To clear the cache navigate to the following URL: http://127.0.0.1:8080/clear_cache

.. note::

    You may need to change the port number above to match your environment


Cancelling a Task
------------------

Some skillets use a background task to perform it's action. If this task appears to be looping or stuck, you can
cancel the task by navigating to the following URL: http://127.0.0.1:8080/cancel_task


Removing a Repository
---------------------

If for some reason, panhandler cannot load a repository, or crashes on the repository details page, you may need
to manually remove the repository. The recommended way to start the panhandler container is to create a
volume mount from your $HOME directory. This ensure all persistent data will be stored in $HOME/.pan_cnc/panhandler. To
manually remove a repository, open a shell and navidate to $HOME/.pan_cnc/panhandler/repositories and use the `rm -rf`
command to remove it completely. You will then need to clear the cache as noted above.


The hammer approach
-------------------

If none of the above things work, you may need to remove everything and start over. First, stop the container


.. code::

    # as a one-linter
    docker ps | grep panhandler | awk '{ print $1 }' | xargs -n 1 docker stop

Next, remove all persistent data

.. code::

    # be careful with this one!
    rm -rf $HOME/.pan_cnc/panhandler

Update to the latest docker image and create a new container

.. code::

    docker pull paloaltonetworks/panhandler:latest
    docker run -t -v $HOME:/root -p 8080:80 paloaltonetworks/panhandler:latest


File a bug
----------

If you need to perform any of the above steps, then this is bug. Please file a bug repot with as much detail as
possible here: https://github.com/paloaltonetworks/panhandler/issues