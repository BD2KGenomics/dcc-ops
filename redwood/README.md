# Redwood

Cloud Data Storage

## Overview

Redwood uses the ICGC Storage System to save and track data bundles in Amazon S3 or an S3-compliant data store. If applicable, server-side encryption is performed behind the scenes, and multipart upload/download are used to improve data transfer times. Each bundle of files includes a _metadata.json_ file that can be used to trigger analysis or workflow result reporting.


## Deploy to Production
You can use the `install_bootstrap` script one directory up to automatically run the setup.

After that, Redwood will already be up and running. You can control the system with the redwood client (in _dcc-ops/redwood/cli/bin/redwood_)
- `redwood up`
- `redwood down`
  - This deletes data!

It will be useful to add _dcc-ops/redwood/cli/bin_ to your PATH.

To confirm proper function: generate an accessToken with `cli/bin/redwood token create` then do a test upload/download from the server:
```
docker run --rm -it --net=redwood_default --link redwood-nginx:storage.redwood.io --link redwood-nginx:metadata.redwood.io \
    -e ACCESS_TOKEN=$(redwood token create) -e REDWOOD_ENDPOINT=redwood.io \
    quay.io/ucsc_cgl/redwood-client:dev bash
$ upload data/someFile
<note the object id outputted>
$ download <objectid> .
```

If everything is as expected, congratulations! You've deployed Redwood.

## Administration
Redwood tracks projects and bundles (collections of files). Users are granted access by being given an access token with certain permission scopes (e.g. upload to project X). Access tokens can be revoked and managed via the auth server.

All projects tracked by redwood must be known to the auth-server. To register a new project:
```
cli/bin/redwood project create PROJECT
```

Authorization is controlled by which scopes a user's access token is granted. To create an access token for a user with certain scopes:
```
cli/bin/redwood token create -s "aws.PROJECT1.upload aws.PROJECT1.download aws.PROJECT2.download" -u "user@ucsc.edu"
# see scripts/createAccessToken.sh -h for more
```

## Development Guide

Run the system for development

### Set Up

You'll need:
- aws secret key and access key
- an s3 bucket
- iam kms encryption (if serverside encryption desired)
- [docker](https://docs.docker.com/engine/installation/linux/ubuntu/) and [docker-compose](https://docs.docker.com/compose/install/)
- this repo cloned locally

Create a `dcc-ops/redwood/.env` file with contents like the following:
```
base_url=redwood.io
email=me@domain

# AWS credentials
access_key=AKIA...
secret_key=asfd...

# AWS S3 bucket for primary data storage and backups
s3_bucket=your-bucket
backup_bucket=your-bucket

# AWS S3 endpoint to reach buckets
s3_endpoint=s3-external-1.amazonaws.com

# AWS IAM Encryption Key id for server-side encryption of S3 data. Comment this out for no SSE
kms_key=0asd...

# root passwords to auth and metadata dbs
auth_db_password=pass
metadata_db_password=password
```

### Development
You can use the `quay.io/ucsc_cgl/redwood-storage-server`, `quay.io/ucsc_cgl/redwood-metadata-server`, and `quay.io/ucsc_cgl/redwood-auth-server` docker images as is or edit the server source and rebuild the images.

It will be helpful to add _dcc-ops/redwood/cli/bin_ to your PATH.

Run the system:
```
redwood up -d
```

In another terminal, test the system:
```
docker run --rm -it --net=redwood_internal --link redwood-nginx:storage.redwood.io --link redwood-nginx:metadata.redwood.io \
    -e ACCESS_TOKEN=$(redwood token create) -e REDWOOD_ENDPOINT=redwood.io \
    quay.io/ucsc_cgl/redwood-client:dev bash
$ upload -p DEV data/someFile
<note the object id outputted>
$ download <objectid> .
```

If that's as expected, things are looking good.

### Admin Tools

Please see [Readme.md](cli/admin/Readme.md) for a more detailed overview of Admin Tools.
