# dcc-ops

## About

This repository contains our Docker-compose and setup bootstrap scripts used to create a deployment of the [UCSC Genomic Institute's](http://ucsc-cgl.org) Cloud Commons implementation on AWS.  The system is designed to receive genomic data, run analysis at scale on the cloud, and return analyzed results to authorized users.  It uses, supports, and drives development of several key GA4GH APIs and open source projects. In many ways it is the generalization of the [PCAWG](https://dcc.icgc.org/pcawg) cloud infrastructure developed for that project.

## Components

The system has components fulfilling a range of functions, all of which are open source and can be used independently or together.

![Cloud Commons Arch](docs/dcc-arch.png)

These components are setup with the install process available in this repository:

* [Spinnaker](spinnaker/README.md): our data submission and validation system
* [Redwood](redwood/README.md): our cloud data storage and indexer based on the ICGC Cloud Storage system
* [Boardwalk](boardwalk/README.md): our file browsing portal on top of Redwood
* [Consonance](consonance/README.md): our multi-cloud orchestration system
* [Action Service](action/README.md): a Python-based toolkit for automating analysis

These are related projects that are either already setup and available for use on the web (e.g. http://dockstore.org) or are used by components above (e.g. Toil workflows from Dockstore).

* [Dockstore](http://dockstore.org): our workflow and tool sharing platform
* [Toil](https://github.com/BD2KGenomics/toil): our workflow engine, these workflows are shared via Dockstore

## Launching the Commons

### Starting an AWS VM

Use the AWS console or command line tool to create a host, I chose:

* r4.large
* 250GB disk
* make a note of your security group name and ID
* your pem key installed somewhere on this box

#### Setup for Redwood

See [README](redwood/README.md) for various tasks that need to be done before running the install_bootstrap script for this system.

### Running the Bootstrap Script

    curl -L https://<url>/install_bootstrap | bash

Until we get a URL to host this one you just do:

    bash install_bootstrap

On the AWS VM.  It will ask you to configure each service.

### Cleaning up Docker Images/Containers/Volumes

This [blog post](https://www.digitalocean.com/community/tutorials/how-to-remove-docker-images-containers-and-volumes) is helpful if you want to clean up previous images/containers/volumes.

## TODO

* should use a reference rather than checkin the consonance directory, that ends up creating duplication which is not desirable 
