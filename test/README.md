# test
dcc-ops test suite

# Overview
The directory contains automated tests that can be run against an installation of the analysis core to confirm proper function.

For now, see `integration.sh`.

## Remove Docker images

Execute the following to remove all running containers, volumes, and stopped images.  This is a potentially distructive process, if you have other non-dcc-ops containers/volumes/images on your machine please do not do this!

    sudo purge_docker.sh
