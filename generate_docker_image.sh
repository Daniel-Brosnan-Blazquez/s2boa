#################################################################
#
# Generate BOA image
#
# Written by DEIMOS Space S.L. (dibb)
#
# module boa
#################################################################

USAGE="Usage: `basename $0` -e path_to_eboa_src -v path_to_vboa_src -d path_to_dockerfile -p path_to_dockerfile_pkg -o path_to_orc_packets -f path_to_eopcfi [-t path_to_tailored] [-a app] [-c boa_tailoring_configuration_path] [-x orc_configuration_path] [-l version]"

########
# Initialization
########
PATH_TO_EBOA=""
PATH_TO_VBOA=""
PATH_TO_TAILORED=""
PATH_TO_DOCKERFILE="Dockerfile"
APP="vboa"
PATH_TO_ORC=""
VERSION="0.1.0"

while getopts e:v:d:p:t:a:o:c:x:p:l:f: option
do
    case "${option}"
        in
        e) PATH_TO_EBOA=${OPTARG}; PATH_TO_EBOA_CALL="-e ${OPTARG}";;
        v) PATH_TO_VBOA=${OPTARG}; PATH_TO_VBOA_CALL="-v ${OPTARG}";;
        t) PATH_TO_TAILORED=${OPTARG}; PATH_TO_TAILORED_CALL="-t ${OPTARG}";;
        d) PATH_TO_DOCKERFILE=${OPTARG}; PATH_TO_DOCKERFILE_CALL="-d ${OPTARG}";;
        p) PATH_TO_DOCKERFILE_PKG=${OPTARG}; PATH_TO_DOCKERFILE_PKG_CALL="-p ${OPTARG}";;
        a) APP=${OPTARG}; APP_CALL="-a ${OPTARG}";;
        o) PATH_TO_ORC=${OPTARG}; PATH_TO_ORC_CALL="-o ${OPTARG}";;
        c) PATH_TO_BOA_TAILORING_CONFIGURATION=${OPTARG}; PATH_TO_BOA_TAILORING_CONFIGURATION_CALL="-c ${OPTARG}";;
        x) PATH_TO_ORC_CONFIGURATION=${OPTARG}; PATH_TO_ORC_CONFIGURATION_CALL="-x ${OPTARG}";;
        l) VERSION=${OPTARG}; VERSION_CALL="-l ${OPTARG}";;
        f) PATH_TO_EOPCFI=${OPTARG};;
        ?) echo -e $USAGE
            exit -1
    esac
done


# Check that option -o has been specified
if [ "$PATH_TO_EOPCFI" == "" ];
then
    echo "ERROR: The option -f has to be provided"
    echo $USAGE
    exit -1
fi

# Check that the path to the eopcfi exists
if [ ! -d $PATH_TO_EOPCFI ];
then
    echo "ERROR: The directory $PATH_TO_EOPCFI provided does not exist"
    exit -1
fi

for library in "libexplorer_data_handling.a" "libexplorer_file_handling.a" "libexplorer_lib.a" "libexplorer_orbit.a" "libexplorer_pointing.a" "libexplorer_visibility.a" "libgeotiff.a" "libproj.a" "libtiff.a" "libxml2.a";
do
    # Check that the library is present
    library_count=$(find $PATH_TO_EOPCFI/lib -maxdepth 1 -mindepth 1 -name $library | wc -l)
    if [ $library_count == 0 ];
    then
        echo "ERROR: The library $PATH_TO_EOPCFI/lib/$library does not exist in the provided eopcfi directory"
        exit -1
    fi
done

for header in "explorer_data_handling.h" "explorer_file_handling.h" "explorer_lib.h" "explorer_orbit.h" "explorer_pointing.h" "explorer_visibility.h";
do
    # Check that the header is present
    header_count=$(find $PATH_TO_EOPCFI/include -maxdepth 1 -mindepth 1 -name $header | wc -l)
    if [ $header_count == 0 ];
    then
        echo "ERROR: The header $PATH_TO_EOPCFI/include/$header does not exist in the provided eopcfi directory"
        exit -1
    fi
done

APP_CONTAINER="boa_app"

# Generate docker image
$PATH_TO_VBOA/generate_docker_image.sh $PATH_TO_EBOA_CALL $PATH_TO_VBOA_CALL $PATH_TO_TAILORED_CALL $PATH_TO_DOCKERFILE_CALL $PATH_TO_DOCKERFILE_PKG_CALL $APP_CALL $PATH_TO_ORC_CALL $PATH_TO_BOA_TAILORING_CONFIGURATION_CALL $PATH_TO_ORC_CONFIGURATION_CALL $VERSION_CALL

# Include the EOP CFI
# Compile source
docker cp $PATH_TO_EOPCFI $APP_CONTAINER:/s2vboa

echo "Compiling EOPCFI..."

docker exec -it $APP_CONTAINER bash -c "gcc -Wno-deprecated -g -fpic -c -DSQLCA_STORAGE_CLASS=static -I /s2vboa/eopcfi/include/ /s2vboa/src/s2boa/eop_cfi/get_footprint.c -o /tmp/get_footprint.o"

echo "Objetcs for the EOPCFI interface generated..."

docker exec -it $APP_CONTAINER bash -c "gcc /tmp/get_footprint.o -Wno-deprecated -g -I /s2vboa/eopcfi/include/ -L /s2vboa/eopcfi/lib/ -lexplorer_visibility -lexplorer_pointing -lexplorer_orbit -lexplorer_lib -lexplorer_data_handling -lexplorer_file_handling -lgeotiff -ltiff -lproj -lxml2 -lm -lc -fopenmp -o /scripts/get_footprint; rm /tmp/get_footprint.o"

# Check that the CFI could be compiled
status=$?
if [ $status -ne 0 ]
then
    echo "The EOP CFI could not be compiled :-("
    exit -1
else
    echo "The EOP CFI has been compiled successfully :-)"
fi

TMP_DIR=`mktemp -d`
# Docker commit and save image
docker commit $APP_CONTAINER boa:$VERSION
docker commit $APP_CONTAINER boa:latest
docker save boa > $TMP_DIR/boa.tar

echo "BOA image exported in: "$TMP_DIR/boa.tar

echo "Removing temporal docker container and image"

docker stop $APP_CONTAINER
docker rm $APP_CONTAINER
docker rmi -f $(docker images boa -q)
