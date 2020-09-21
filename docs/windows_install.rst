Windows Installation
====================

Running panhandler on windows is possible through docker. The most reliable setup method at this time is to run docker commands directly through powershell backed by WSL2. This process will require multiple reboots so plan accordingly. Other installation methods may not provide appropriate access to the docker daemon from the running panhandler container resulting in certain skillet types not functioning.

Install WSL2
-------------

Begin by installing WSL2. Microsoft has a good document on how to do this here,

https://docs.microsoft.com/en-us/windows/wsl/install-win10

If unsure about a Linux distribution to use, choose ubuntu. Verify you can access WSL2 before continuing.
 
Install Docker Desktop
-----------------------
 
After WSL2 functionality is verified, install the latest docker desktop for windows using the following tutorial from docker.

https://docs.docker.com/docker-for-windows/install/

During the install Ensure the following settings. 
	- Use the WSL 2 based engine, using "Hyper-V" may lead to some known problems
	- Start Docker Desktop when you login, it will allow panhandler to auto start on boot
	- DO NOT select "Expose daemon on tcp://localhost:2375 without TLS"
	- DO NOT select "Enable experimental features"
	- DO NOT enable "Kubernetes"
	
Unless the installer states otherwise, these settings can be updated by right clicking the docker icon in your system tray and selecting "settings".

Although WSL2 is required for operation, you will not be using WSL2 to talk to docker. Open powershell and type "docker ps" to verify your docker cli is working and able to talk to the docker daemon, you should see output similar to this with no errors. This has to be working before you can proceed.

.. image:: images/ph-windows-1.png

Another good test to perform to ensure docker is running fine is to run the docker "Hello world" image. From powershell type this command:

.. code-block:: powershell

  docker run --rm -it hello-world

You should get an output similar to this:

.. image:: images/ph-windows-2.png

Install Panhandler
------------------

At this point you are ready to install and start panhandler. In powershell issue this command to pull down the latest panhandler image.

docker pull paloaltonetworks/panhandler:latest

This will take a minute, but you should get output similar to this:

.. image:: images/ph-windows-3.png

With the image downloaded all that's left to do is create the volumes and start panhandler. Docker volumes are virtual storage entities that provides a way to upgrade the image without losing app data. Create the volumes by running these commands,

.. code-block:: powershell

  docker volume create CNC_VOLUME
  docker volume create PANHANDLER_VOLUME

You can verify the volumes have been created by running this command,

.. code-block:: powershell

  docker volume list

.. image:: images/ph-windows-4.png

Now you can start panhandler by coping this entire command block into powershell. This command sets a restart policy of always which ensures panhandler will restart with your computer and always run unless you stop it.

.. code-block:: powershell

  docker run `
	  --name panhandler `
	  -v //var/run/docker.sock:/var/run/docker.sock `
	  -v PANHANDLER_VOLUME:/home/cnc_user `
	  -v CNC_VOLUME:/home/cnc_user/.pan_cnc `
	  -d -p 8080:8080 `
	  --restart=always `
	  paloaltonetworks/panhandler:latest
	
That command will result in a long hash that will serve as the ID for the container, but you can still reference it with the name "panhandler"

.. image:: images/ph-windows-5.png

After a few seconds, you should be able to access panhandler in your web browser by browsing to:

http://localhost:8080/

The installation process is now complete.

Stopping and Starting Panhandler
--------------------------------

If you wish to stop panhandler from running until you restart it, you can do so with the powershell command

.. code-block:: powershell

  docker stop panhandler

Likewise, this process can be restarted with the command

.. code-block:: powershell

  docker start panhandler

Upgrading Panhandler
--------------------

Only one more command is required to upgrade panhandler. The process is to delete the old container, update the image, and start a new container.

You can delete the old container, running or stopped, with this command,

.. code-block:: powershell

  docker container rm panhandler -f

.. image:: images/ph-windows-6.png

You then can use the 'docker pull' and 'docker run' commands exactly as they are above to download a newer panhandler image and start it. The volumes you created earlier will be still be available and assigned to the new container if you use the commands as they are.

