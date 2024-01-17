#!/bin/sh

# Set the color variables
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

FILE=./docker-compose.yml
if test -f "$FILE"; then
    line=$(head -n 1 $FILE)
    if [ "$line" = "# kafka installation for capitalist" ]; then
        docker compose rm -svf
        if [ $? -ne 0 ]; then
            echo "${red}docker-compose failed to remove psql container${clear}"
            exit 1
        fi        
        docker compose up -d
        if [ $? -ne 0 ]; then
            echo "${red}docker-compose failed start container${clear}"
            exit 1
        fi
        python3 setup_kafka.py
    fi
fi