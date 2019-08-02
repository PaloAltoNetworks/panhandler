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
export FORCE_DEFAULT_PORT=false

while getopts ":t:r:p:h" opt; do
  case ${opt} in
    t)
        IMAGE_TAG="$OPTARG"
    ;;
    p)
        DEFAULT_PORT="$OPTARG"
        FORCE_DEFAULT_PORT=true
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

if [[ ! $(command -v docker) ]];
  then
    echo "Could not find the docker command, please ensure you have docker installed on this machine"
    exit 1
fi

echo "==================================================================================================="
echo " "
echo "  Welcome to Panhandler"
echo " "

if [[ ${IMAGE_TAG} == latest ]];
 then
    PANHANDLER_ID=$(docker ps -a |
                            grep -v 'panhandler:dev' |
                            grep -v 'panhandler:beta' |
                            grep -v 'panhandler:v' |
                            grep 'paloaltonetworks/panhandler' |
                            awk '{ print $1 }'
                           )
    export PANHANDLER_ID
    # now that we (maybe?) have the container ID, ensure we use the latest tag from here on out
    PANHANDLER_IMAGE=paloaltonetworks/panhandler:latest
    export PANHANDLER_IMAGE
 else
    PANHANDLER_IMAGE=paloaltonetworks/panhandler:${IMAGE_TAG}
    PANHANDLER_ID=$(docker ps -a |
                            grep "${PANHANDLER_IMAGE}" |
                            awk '{ print $1 }'
                           )
    export PANHANDLER_ID
    export PANHANDLER_IMAGE
fi

echo "Found container id of ${PANHANDLER_ID}"

echo "  Checking for updates ... (This may take some time while the image downloads)"
echo " "

docker pull "${PANHANDLER_IMAGE}" | grep 'Image is up to date'

# shellcheck disable=SC2181
if [[ $? -eq 0 ]];
 then
    echo " "
    echo "  ${PANHANDLER_IMAGE} is already up to date!"
    echo " "
else
    echo "  Panhandler is out of date, and will need to be restarted"
    echo " "
    NEEDS_UPDATE=true
fi

if [[ ${RESET_REPOSITORIES} == true ]];
 then
    echo "  Moving Panhandler data directory to backup"
    echo " "
    echo " "
    echo " "
    DATESTRING=$(date "+%Y-%m-%d-%H:%M:%S")
    # shellcheck disable=SC2086
    mv ~/.pan_cnc/panhandler ~/.pan_cnc/panhandler.backup.${DATESTRING}
    mkdir ~/.pan_cnc/panhandler
fi


if [[ -z "${PANHANDLER_ID}" ]];
 then
    echo "  Panhandler:${IMAGE_TAG} has not been started"
    echo " "
#    FIXME to add additional checks and to come up with an available port
#    docker ps -a | grep -q "${DEFAULT_PORT}->80"
#    if [[ $? -eq 0 ]];
#     then
#     echo " Default port of 8080 is taken "
#    fi
else
    # Panhandler container has been created already and we have a valid container id
    # Let's verify if it's running
    CONTAINER_RUNNING=$( docker inspect "${PANHANDLER_ID}" -f '{{ .State.Running }}')
    export CONTAINER_RUNNING
    if [[ ${CONTAINER_RUNNING} == true ]];
      then
        # now, let's check if we should stop and remove it
        if [[ ${NEEDS_UPDATE} == true ]];
         then
            #
            # Set the port to the value the user is already using
            #
            if [[ ${FORCE_DEFAULT_PORT} == false ]];
             then
                echo "Getting existing port mapping for re-use"
                DEFAULT_PORT=$(docker port "${PANHANDLER_ID}" | grep '80/tcp'| cut -d':' -f2)
                echo "Using ${DEFAULT_PORT} as local port mapping"
            fi
            echo "  Stopping Panhandler container"
            echo " "
            docker stop "${PANHANDLER_ID}"

            echo "  Removing old Panhandler container"
            echo " "
            docker rm -f "${PANHANDLER_ID}"

        else
            echo "  Panhandler is already up to date and is currently running"
            echo " "
            echo "  Currently Running containers:"
            echo " "
            docker ps
            echo " "
            echo "==================================================================================================="
            exit 0
        fi
    else
        echo "  Restarting Panhandler..."
        echo " "
        docker start "${PANHANDLER_ID}" >>/dev/null 2>&1
        docker ps
        echo " "
        echo "==================================================================================================="
        exit 0
    fi
fi

echo "  Creating and running new Panhandler container"
echo " "
if [[ ${IMAGE_TAG} == latest ]];
 then
    # shellcheck disable=SC2086
    docker run -p ${DEFAULT_PORT}:80 -t -v "$HOME":/root -d -n panhandler ${PANHANDLER_IMAGE}
else
    # this is only necessary while 2.3 is in development
    # shellcheck disable=SC2086
    docker run -p ${DEFAULT_PORT}:8080 -t -v "$HOME":/home/cnc_user -d -n panhandler ${PANHANDLER_IMAGE}
fi
echo " "
echo " "
echo " "
echo " "
echo "  You may now use Panhandler by opening a web browser and browsing to http://localhost:${DEFAULT_PORT}"
echo " "
echo " "
echo " "
echo " "
