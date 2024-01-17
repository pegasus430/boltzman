#!/bin/sh
# Production deployment script entry point
# Color variables
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
blue='\033[0;34m'
magenta='\033[0;35m'
cyan='\033[0;36m'
# Clear the color after that
clear='\033[0m'

#return code check
check_return()
{
    if [ $? -ne 0 ]; then
        echo "${red}$1r${clear}"
        exit 1
    fi        
}
name=$(basename "$1")


# Create stage dir
rm -rf ./stage
mkdir stage
mkdir stage/service_code
mkdir stage/service_code/logs

# copy target service 
cp -r ../config ./stage/service_code
cp -r ../core ./stage/service_code
cp -r ../exceptions ./stage/service_code
cp -r ../genes ./stage/service_code
cp -r ../intake ./stage/service_code
cp -r ../mutators ./stage/service_code
cp -r ../intake ./stage/service_code
cp -r ../psql ./stage/service_code
cp -r ../server ./stage/service_code
cp -r ../workers ./stage/service_code
cp -r ../utils ./stage/service_code
cp -r ../tests ./stage/service_code
cp -r ../requirements.txt ./stage/service_code
cp ../VERSION ./stage
cp -r ../service_images ./stage/service_code
mkdir ./stage/service_code/model_data


# copy dokcer template and replace service name file
cp ../docker_templates/Service  ./stage/Dockerfile
cd stage

#get version
pwd
version=`cat ./VERSION`

#build service image
docker image build -t $name:$version ./

# clean up
cd ..
rm -rf ./stage


