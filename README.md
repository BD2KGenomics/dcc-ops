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

### Running the Bootstrap Script

    curl -L https://install.perlbrew.pl | bash
