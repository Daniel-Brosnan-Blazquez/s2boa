#################################################################
#
# Init docker environment of the s2boa based on the script of vboa
#
# Written by DEIMOS Space S.L. (dibb)
#
# module vboa
#################################################################

USAGE="Usage: `basename $0` -e path_to_eboa_src -v path_to_vboa_src -d path_to_dockerfile -o path_to_orc_packets -f path_to_eopcfi [-p port] [-t path_to_tailored] [-l containers_label] [-a app] [-c boa_tailoring_configuration_path] [-c orc_tailoring_configuration_path]"

########
# Initialization
########
PATH_TO_EBOA=""
PATH_TO_VBOA=""
PATH_TO_TAILORED=""
PATH_TO_DOCKERFILE="Dockerfile"
PORT="5000"
CONTAINERS_LABEL="dev"
APP="vboa"
PATH_TO_ORC=""

while getopts e:v:d:p:t:l:a:o:c:x:f: option
do
    case "${option}"
        in
        e) PATH_TO_EBOA=${OPTARG};;
        v) PATH_TO_VBOA=${OPTARG};;
        t) PATH_TO_TAILORED=${OPTARG};;
        d) PATH_TO_DOCKERFILE=${OPTARG};;
        p) PORT=${OPTARG};;
        l) CONTAINERS_LABEL=${OPTARG};;
        a) APP=${OPTARG};;
        o) PATH_TO_ORC=${OPTARG};;
        c) PATH_TO_BOA_TAILORING_CONFIGURATION=${OPTARG};;
        x) PATH_TO_ORC_CONFIGURATION=${OPTARG};;
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

# Check that the last folder of the path to the eopcfis is eopcfi
if [ "$(basename $PATH_TO_EOPCFI)" != "eopcfi" ];
then
    echo "ERROR: The last directory of the path $PATH_TO_EOPCFI should be eopcfi"
    exit -1
fi

# Initialize docker environment using he command from vboa
$PATH_TO_VBOA/init_docker_dev_environment.sh -e $PATH_TO_EBOA -v $PATH_TO_VBOA -d $PATH_TO_DOCKERFILE -p $PORT -t $PATH_TO_TAILORED -a $APP -c $PATH_TO_BOA_TAILORING_CONFIGURATION -l $CONTAINERS_LABEL -o $PATH_TO_ORC -x $PATH_TO_ORC_CONFIGURATION

##################
# Install EOPCFI #
##################
APP_CONTAINER="boa-app-$CONTAINERS_LABEL"
# Compile source
docker cp $PATH_TO_EOPCFI $APP_CONTAINER:/s2vboa

echo "Compiling EOPCFI..."

docker exec -it $APP_CONTAINER bash -c "gcc -Wno-deprecated -g -fpic -c -DSQLCA_STORAGE_CLASS=static -I /s2vboa/eopcfi/include/ /s2vboa/src/s2boa/eop_cfi/get_footprint.c -o /tmp/get_footprint.o"

echo "Objetcs for the EOPCFI interface generated..."

docker exec -it $APP_CONTAINER bash -c "gcc /tmp/get_footprint.o -Wno-deprecated -g -I /s2vboa/eopcfi/include/ -L /s2vboa/eopcfi/lib/ -lexplorer_visibility -lexplorer_pointing -lexplorer_orbit -lexplorer_lib -lexplorer_data_handling -lexplorer_file_handling -lgeotiff -ltiff -lproj -lxml2 -lm -lc -fopenmp -o /scripts/get_footprint; rm /tmp/get_footprint.o"

echo "Compilation of the EOPCFI interface successfully done :-)"
