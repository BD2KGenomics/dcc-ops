#! /bin/bash

set -o errexit
set -o pipefail
set -o nounset
# set -o xtrace

if [ -e /etc/rc.local ]
then
    #add the command to
    #start the UCSC Computational Genomics Platform (CGP) container that sets up the 
    #Nginx config template with the uuids for each of the containers in the CGP
    #at boot time
    #See dcc-ops/common/base.yml for more details
    if ! grep -Fxq "sudo docker start core-config-gen" /etc/rc.local
    then
        sed -i -e '$i \
#start the UCSC Computational Genomics Platform (CGP) container that sets up the\
#Nginx config template with the uuids for each of the containers in the CGP\
#See dcc-ops/common/base.yml for more details\
sudo docker start core-config-gen\n'\
        /etc/rc.local

        echo "Added docker start core-config-gen command to /etc/rc.local"       
    else
        echo "Found docker start core-config-gen or similar command in /etc/rc.local \
so it was not added"
    fi
else
    echo "WARNING: No /etc/rc.local file exists; the command 'sudo docker start \
core-config-gen' should be manually run after booting up"
fi

