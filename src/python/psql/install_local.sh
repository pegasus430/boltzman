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
cp ../docker_templates/Psql ./dockerfile
docker image build -t psql_docker ./
docker run -p 5433:5432 --name psql_db --network boltzman -d psql_docker

