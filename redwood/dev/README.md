# dcc-redwood-compose
ICGC Storage System Adapted for UCSC in Docker Compose

## Overview
This project runs the Redwood storage-server, metadata-server, and auth-server (closely based off of ICGC's storage system servers) as well as the MongoDB and PostgreSQL databases that the servers require.

## Run the System for Development
You'll need maven (3.2.5), docker, and docker-compose installed.

This project composes the two requisite databases and the `ucsc-storage-server`, `ucsc-metadata-server`, and `ucsc-auth-server` Docker images into a 5-container docker-compose setup.The _ucsc-*-server_ images should be built on the current machine. To build them, clone the _dcc-storage_, _dcc-metadata_, and _dcc-auth_ repositories and run the following from a directory containing _dcc-storage_, _dcc-metadata_, and _dcc-auth_:

```
cd dcc-storage && ./mvnw && tar xvf dcc-storage-server/target/*-dist.tar.gz && docker build -t redwood-storage-server dcc-storage-server-*-SNAPSHOT; rm -r dcc-storage-*-SNAPSHOT; cd ..
cd dcc-metadata && ./mvnw && tar xvf dcc-metadata-server/target/*-dist.tar.gz && docker build -t redwood-metadata-server dcc-metadata-server-*-SNAPSHOT; rm -r dcc-metadata-*-SNAPSHOT; cd ..
cd dcc-auth && ./mvnw && tar xvf dcc-auth-server/target/*-dist.tar.gz && docker build -t redwood-auth-server dcc-auth-server-*-SNAPSHOT; rm -r dcc-auth-*-SNAPSHOT; cd ..
```

Then you can start the system with: `docker-compose up` and stop it with `docker-compose down`.

_Note:_ A `~/.aws/credentials` file is assumed by `docker-compose.yml` to exist on the host.
