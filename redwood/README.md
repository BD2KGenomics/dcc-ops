# Redwood

Cloud Data Storage

## Overview

Redwood uses the ICGC Storage System to save and track data bundles in Amazon S3 or an S3-compliant data store. If applicable, server-side encryption is performed behind the scenes, and multipart upload/download are used to improve data transfer times. Each bundle of files includes a _metadata.json_ file that can be used to trigger analysis or workflow result reporting.

## Setup with the Bootstrapper

You can use the `install_bootstrap` script one directory up to automatically run the setup.  You still need to perform the AWS tasks described below.

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

From _dcc-ops/redwood_, run the system:
```
docker-compose -f base.yml -f dev.yml up
```

In another terminal, test the system (this has to be done from the dcc-ops/redwood directory unless you create your accessToken separately):
```
docker run --rm -it --net=redwood_default --link redwood-nginx:storage.redwood.io --link redwood-nginx:metadata.redwood.io \
    -e ACCESS_TOKEN=$(scripts/createAccessToken.sh) -e REDWOOD_ENDPOINT=redwood.io \
    quay.io/ucsc_cgl/redwood-client:dev bash
$ upload -p DEV data/someFile
<note the object id outputted>
$ download <objectid> .
```

If that's as expected, things are looking good.


## Deploy to Production
This is a guide for deploying Redwood to production on AWS.

_Note:_ Create bucket, ec2, encryption key, etc. in the same region.
- Region: Oregon (us-west-2)

Create the storage system S3 bucket. This will hold all the storage system data.
- Bucket Name: redwood-2.0.1
- Region: Oregon
- Logging Enabled: true
- Logging Target Bucket: redwood-2.0.1
- Logging Target Prefix: logs/

Create an IAM user to embody the storage service
- User Name: redwood

Create a IAM KMS Encryption Key to encrypt S3 data.
- Key Alias: redwood-2-0-1-master-key
- Key Administrators: you
- Key Users: redwood
  - This is the user just created

Create the storage system server.
- OS: Ubuntu
- RAM: 16GB+ recommended
- SSH Key Pair: <your key pair>

Set up the server's security group (_redwood-server_)
- Accept incoming request to port 443.

Connect to the EC2.
- `ssh ubuntu@your-server`

Prepare the system.
- install [docker](https://docs.docker.com/engine/installation/linux/ubuntu/) and [docker-compose](https://docs.docker.com/compose/install/)

Point your domain to your server
- URLs _storage.yourdomain.com_, _auth.yourdomain.com_, and _metadata.yourdomain.com_ should resolve to your ec2.

Copy or clone this project (_dcc-redwood-compose_) over to the the ec2
- `git clone git@github.com:BD2KGenomics/dcc-redwood-compose.git`

Update all properties in _dcc-ops/redwood/.env_.
- See the inline comments
- If on open stack or not intending to use server-side encryption, comment out _kms_key_
- Daily backups of all metadata and auth data will be uploaded to the S3 bucket specified by backup_bucket. This should be properly access-controlled.

Run the system (from the _dcc-ops/redwood_ directory)
- `docker-compose -f base.yml -f prod.yml up -d`
- You should schedule this command to run on boot as an upstart/systemd job

At this point, Redwood should be up and running.

To confirm this: generate an accessToken with `scripts/createAccessToken.sh` then do a test upload/download from the server:
```
docker run --rm -it --net=redwood_default --link redwood-nginx:storage.redwood.io --link redwood-nginx:metadata.redwood.io \
    -e ACCESS_TOKEN=<your_access_token> -e REDWOOD_ENDPOINT=redwood.io \
    quay.io/ucsc_cgl/redwood-client:dev bash
$ upload data/someFile
<note the object id outputted>
$ download <objectid> .
```

If everything is as expected, congratulations! You've deployed Redwood.
