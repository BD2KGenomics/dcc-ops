#!/bin/bash

docker kill $(docker ps -a -q)
docker rmi $(docker images -a -q)
docker rm $(docker ps -a -f status=exited -q)
docker volume rm $(docker volume ls -f dangling=true -q)

