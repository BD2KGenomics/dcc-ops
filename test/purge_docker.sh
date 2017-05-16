#!/bin/bash

docker kill $(docker ps -a -q)
docker rmi $(docker images -a -q)
docker rmi $(docker images -q -f dangling=true)
docker rm $(docker ps -a -f status=exited -q)
docker volume rm $(docker volume ls -f dangling=true -q)

#Remove files stored in local volumes by the boardwalk components
#and the actions service

sudo rm -r /root/dcc-dashboard-service
sudo rm -r /root/dcc-metadata-indexer
sudo rm -r /root/dcc-actions-service
