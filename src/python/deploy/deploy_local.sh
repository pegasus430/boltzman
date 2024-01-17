#!/bin/sh
# local deployment script entry point
# this script spins containers for essential services on your local docker

# Color variables
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
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

# Psql
cd ../psql
./install_local.sh
check_return "local postgres installation failed"


# Kafka
cd ../kafka_
./install_local.sh
check_return "local kafka installation failed"

# Service Status Monitor




