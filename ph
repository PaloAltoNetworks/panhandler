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
export CNC_VOLUME=pan_cnc_volume

# used for filtering containers
export DEV_EXPOSED_PORT=8080
export LATEST_EXPOSED_PORT=8080

# default panhandler auth
export CNC_USERNAME=paloalto
export CNC_PASSWORD=panhandler

function ensure_docker_volume {
  if [[ ! $(docker volume ls -q -f name=$CNC_VOLUME) ]];
  then
    echo "Creating data volume"
    docker volume create $CNC_VOLUME
  fi
}

function validate_container_id {
  # container id will always be 13 characters. Anything is either blank or an error message along the way
  # example: b977b1401f9e
  PH_ID=$1
  echo " " >&2
  echo "  Checking ${PH_ID}" >&2
  if [[ -z $PH_ID ]];
  then
    return 1
  fi

  len=$(echo $1 | wc -c | sed -e 's/ //g')
  if [[ $len -eq '13' ]];
  then
    return 0
  else
    return 1
  fi
}

function find_panhandler_container_id {

  # first check for a name and ancestor
  PANHANDLER_ID=$(docker ps -a -q -f name=panhandler -f ancestor="$PANHANDLER_IMAGE")
  if validate_container_id "${PANHANDLER_ID}";
  then
    echo "${PANHANDLER_ID}"
    return 0
  fi
  # maybe name hasn't been set but we have the right image here
  PANHANDLER_ID=$(docker ps -a -q -f ancestor="$PANHANDLER_IMAGE")
  if validate_container_id "${PANHANDLER_ID}";
  then
    echo "${PANHANDLER_ID}"
    return 0
  fi
  # in the following cases, maybe the user has pulled a new image in which case we can no longer see the ancestor image
  # we will have to filter images using the known exposed ports
  # ancestor is no longer available after a pull, check for a name being set and the exposed port
  PANHANDLER_ID=$(docker ps -a -q -l -f name=panhandler -f expose="${EXPOSED_PORT}")
  if validate_container_id "${PANHANDLER_ID}";
  then
    # since the acenstor is incorrect, we know we're gonna need to stop, rm, and recreate
    NEEDS_UPDATE=true
    export NEEDS_UPDATE
    echo "${PANHANDLER_ID}"
    return 0
  fi
  # ok, no ancestor and no name is set either :-|
  # filter on known command string, known exposed port, and ensure a published port (grep tcp ensures this)
  # finally, only return the first match found in case we have more than 1 for some reason...
  PANHANDLER_ID=$(docker ps -a --format "{{.ID}} {{.Command}} {{ .Ports}}" -f expose="${EXPOSED_PORT}" |
                  grep '/app/cnc/start_app' |
                  grep 'tcp' |
                  head -1 |
                  awk '{ print $1} '
                  )
  if validate_container_id "${PANHANDLER_ID}";
  then
    # since the acenstor is incorrect, we know we're gonna need to stop, rm, and recreate
    NEEDS_UPDATE=true
    export NEEDS_UPDATE
    echo "${PANHANDLER_ID}"
    return 0
  fi

  # at this point we can be reasonably sure panhandler does not exist on this instance in some form or fashion
  return 1
}

function container_has_correct_image {
  FOUND=$(docker ps -a -q -f id="$PANHANDLER_ID" -f ancestor="$PANHANDLER_IMAGE")
  if validate_container_id "$FOUND";
  then
    return 0
  fi
  # this container has an out of date image
  return 1
}

function create_panhandler_container {
  echo "  Creating and running new Panhandler container"
  echo " "
  if [[ ${IMAGE_TAG} == latest ]];
   then
      # shellcheck disable=SC2086
      docker run -p ${DEFAULT_PORT}:${LATEST_EXPOSED_PORT} -t -v "$HOME":/root -d -e CNC_USERNAME -e CNC_PASSWORD --name panhandler ${PANHANDLER_IMAGE}
  else
      # this is only necessary while 2.3 is in development
      # shellcheck disable=SC2086
      ensure_docker_volume
      docker run -p "${DEFAULT_PORT}":${DEV_EXPOSED_PORT} -t -d -v "$CNC_VOLUME":/home/cnc_user/.pan_cnc \
              -e CNC_USERNAME \
              -e CNC_PASSWORD \
              --name "panhandler_${IMAGE_TAG}" "${PANHANDLER_IMAGE}"
  fi
  return 0
}

function get_existing_published_port {
    FOUND_PORT=$(docker inspect "${PANHANDLER_ID}" |
                  grep "HostPort" |
                  head -1 |
                  awk '{ print $2 }' |
                  sed -e 's/"//g')
    if [[ -n $FOUND_PORT ]];
    then
      echo "$FOUND_PORT"
    else
      echo "$DEFAULT_PORT"
    fi
}

while getopts ":t:r:p:w:u:h" opt; do
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
    w)
        CNC_PASSWORD="$OPTARG"
    ;;
    u)
        CNC_USERNAME="$OPTARG"
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
echo "==================================================================================================="

if [[ ${IMAGE_TAG} == latest ]];
 then
    EXPOSED_PORT=${LATEST_EXPOSED_PORT}
    export EXPOSED_PORT

    # now that we (maybe?) have the container ID, ensure we use the latest tag from here on out
    PANHANDLER_IMAGE=paloaltonetworks/panhandler:latest
    export PANHANDLER_IMAGE

    PANHANDLER_ID=$(find_panhandler_container_id)
    export PANHANDLER_ID

 else
    EXPOSED_PORT=${DEV_EXPOSED_PORT}
    export EXPOSED_PORT

    PANHANDLER_IMAGE=paloaltonetworks/panhandler:${IMAGE_TAG}
    export PANHANDLER_IMAGE

    # fix for returning more than 1 container. This returns only the latest created container
    PANHANDLER_ID=$(find_panhandler_container_id)
    export PANHANDLER_ID

fi


echo " "
echo "  Checking for image updates ... (This may take some time while the image downloads)"

docker pull "${PANHANDLER_IMAGE}" | grep 'Image is up to date' >/dev/null

# shellcheck disable=SC2181
if [[ $? -eq 0 ]];
 then
    echo " "
    echo "  ${PANHANDLER_IMAGE} is already up to date!"
else
    echo "  Panhandler is out of date, and will need to be restarted"
    echo " "
    NEEDS_UPDATE=true
fi

if [[ ${RESET_REPOSITORIES} == true ]];
 then
    echo " "
    echo "  Moving Panhandler data directory to backup"
    DATESTRING=$(date "+%Y-%m-%d-%H:%M:%S")
    # shellcheck disable=SC2086
    mv ~/.pan_cnc/panhandler ~/.pan_cnc/panhandler.backup.${DATESTRING}
    mkdir ~/.pan_cnc/panhandler
fi


if [[ -z "${PANHANDLER_ID}" ]];
 then
    echo " "
    echo "  ${PANHANDLER_IMAGE} has not been started..."
    create_panhandler_container
else
  echo " "
  echo "  Found container id of ${PANHANDLER_ID}"
  # we have a valid conatiner id from a previous run, let's ensure it has the correct image as it's ancestor
  if container_has_correct_image;
  then
    echo " "
    echo "  This container is up-to-date!"
    NEEDS_UPDATE=false
  else
    echo " "
    echo "  This container is out-of-date"
    NEEDS_UPDATE=true
  fi

  if [[ ${NEEDS_UPDATE} == true ]];
   then
      #
      # Set the port to the value the user is already using
      #
      if [[ ${FORCE_DEFAULT_PORT} == false ]];
       then
          echo " "
          echo "  Getting existing port mapping for re-use"
          # convert "HostPort": "8080" into 8080
          DEFAULT_PORT=$(get_existing_published_port)
          echo " "
          echo "  Using ${DEFAULT_PORT} as local port mapping"
      fi
      echo " "
      echo "  Stopping Panhandler container"
      docker stop "${PANHANDLER_ID}"

      echo " "
      echo "  Removing old Panhandler container"
      docker rm -f "${PANHANDLER_ID}"

      create_panhandler_container
  else
      DEFAULT_PORT=$(get_existing_published_port)
      echo " "
      echo "  Panhandler is already up to date. Ensuring it's running"
      docker start "${PANHANDLER_ID}" >>/dev/null 2>&1
  fi
fi

echo " "
echo "  You may now use Panhandler by opening a web browser and browsing to http://localhost:${DEFAULT_PORT}"
echo " "
echo "==================================================================================================="
