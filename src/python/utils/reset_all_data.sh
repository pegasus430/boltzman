#!/bin/sh
cd ../kafka_
./install_local.sh
cd ../utils
python3 ./seed_networks.py reset
# clear logs
find /dir/to/search/ -type d -name "dirName"
