#!/bin/bash

########################################################################################################################
#
#   Panhandler start up tool
#
#   This script will check for updates to the paloaltonetworks/panhandler image and start / restart / recreate
#   the panhandler container as necessary
#
#   Feel free to leave feedback at: https://github.com/PaloAltoNetworks/panhandler/issues
#
########################################################################################################################

export IMAGE_TAG=latest
export DEFAULT_PORT=8080
export RESET_REPOSITORIES=false
export NEEDS_UPDATE=false

while getopts ":t:r:p:h" opt; do
  case ${opt} in
    t)
        IMAGE_TAG="$OPTARG"
    ;;
    p)
        DEFAULT_PORT="$OPTARG"
    ;;
    r)
        RESET_REPOSITORIES="$OPTARG"
    ;;
    h)
        echo "Valid options are: "
        echo "-t Image tag (latest, dev, beta)"
        echo "-p local port binding, default is 8080 *note this will be ignored if the container is already running"
        echo "-r Reset Panhandler local settings (true, false)"
        echo "Reset will remove all imported repositories, local caches, and environments"
        exit 0
    ;;
    \?)
        echo "Invalid option -$OPTARG" >&2
    ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

case ${IMAGE_TAG} in
    latest)
        ;;
    dev)
        ;;
    beta)
        ;;
     \?)
        echo "Invalid tag - Please use latest, dev, or beta"
        exit 1
        ;;
esac

echo "==================================================================================================="
echo " "
echo "Welcome to Panhandler"
echo " "

export PANHANDLER_ID=$(docker ps -a | grep ${PANHANDLER_IMAGE} | awk '{ print $1 }')

export PANHANDLER_IMAGE=paloaltonetworks/panhandler:${IMAGE_TAG}
echo "Checking for updates ... (This may take some time while the image downloads)"
echo " "

docker pull ${PANHANDLER_IMAGE} | grep 'Image is up to date'

if [[ $? -eq 0 ]];
 then
    echo " "
    echo "${PANHANDLER_IMAGE} is already up to date!"
    echo " "
else
    echo "Panhandler is out of date, and will need to be restarted"
    echo " "
    NEEDS_UPDATE=true
fi

if [[ ${RESET_REPOSITORIES} == true ]];
 then
    echo "Moving Panhandler data directory to backup"
    echo " "
    echo " "
    echo " "
    DATESTRING=$(date "+%Y-%m-%d-%H:%M:%S")
    mv ~/.pan_cnc/panhandler ~/.pan_cnc/panhandler.backup.${DATESTRING}
    mkdir ~/.pan_cnc/panhandler
fi


if [[ -z "${PANHANDLER_ID}" ]];
 then
    echo "Panhandler:${IMAGE_TAG} has not been started"
    echo " "
else
    # Panhandler container has been created already, let's check if we should stop and remove it
    if [[ ${NEEDS_UPDATE} == true ]];
     then
        echo "Stopping Panhandler container"
        echo " "
        docker stop ${PANHANDLER_ID}

        echo "Removing old Panhandler container"
        echo " "
        docker rm -f ${PANHANDLER_ID}
    else
        # no need to update, and it's aready been defined, let's check if it's actually running
        docker ps | grep -q ${PANHANDLER_IMAGE}
        if [[ $? -eq 0 ]];
          then
            echo "Panhandler is already up to date and is currently running"
            echo " "
            echo "Currently Running containers:"
            echo " "
            docker ps
            echo " "
            echo "==================================================================================================="
            exit 0
        else
            echo "Restarting Panhandler..."
            docker start ${PANHANDLER_ID}
            echo " "
            echo "==================================================================================================="
            exit 0
        fi
    fi
fi

echo "Creating and running new Panhandler container"
echo " "
if [[ ${IMAGE_TAG} == latest ]];
 then
    docker run -p ${DEFAULT_PORT}:80 -t -v $HOME:/root -d ${PANHANDLER_IMAGE}
else
    # this is only necessary while 2.3 is in development
    docker run -p ${DEFAULT_PORT}:80 -t -v $HOME:/home/cnc_user -d ${PANHANDLER_IMAGE}
fi
echo " "
echo " "
echo " "
echo "You may now use Panhandler by opening a web browser and browsing to http://localhost:${DEFAULT_PORT}"
echo " "
echo " "
echo " "
