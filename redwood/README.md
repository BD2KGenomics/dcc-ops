# Redwood

Cloud Data Storage

## Overview

Redwood uses the ICGC Storage System to save and track data bundles in Amazon S3 or an S3-compliant data store. If applicable, server-side encryption is performed behind the scenes, and multipart upload/download are used to improve data transfer times. Each bundle of files includes a _metadata.json_ file that can be used to trigger analysis or workflow result reporting.

## Setup with the Bootstrapper

You can use the `install_bootstrap` script one directory up to automatically run the setup.  You still need to perform the AWS tasks described below.

## Development Guide

Run the system for development

### Set Up

Create an S3 bucket and IAM KMS encryption key, make a note of both.  Have the AWS access key and secret key of whichever account you want to use to run the system (probably your own) ready.

#### On AWS

Create an S3 bucket where the storage system will put all its data.
- Note the name and region you use

Create an IAM (KMS) Encryption Key.
- Create it in the same region as your S3 bucket
- Give yourself (at least) permission to manage the key
- Give yourself and the storage system user (if different) permission to use the key
- Note the id of the key

#### On the Host Running Redwood

Put your (or whichever account's credentials will be used to run the storage system) AWS access key and secret key in a _~/.aws/credentials_ file.
```
sudo apt-get install -y python-pip && sudo pip install awscli && aws configure
```

Install [docker](https://docs.docker.com/engine/installation/linux/ubuntu/) and [docker-compose](https://docs.docker.com/compose/install/).

Clone this project.
```
cd && sudo apt-get install -y git && git clone https://github.com/BD2KGenomics/dcc-ops.git
```

Edit the following properties in the _dcc-ops/redwood/.env_ file. See the inline comments.
- _s3_bucket_
- _s3_endpoint_
- _kms_key_
  - If on open stack or not intending to use server-side encryption, comment out this property

### Run the System for Development
From _dcc-ops/redwood_, run the system:
```
docker-compose -f base.yml -f dev.yml up
```

_Note:_ For storage system development you should edit code then build the `quay.io/ucsc_cgl/redwood-storage-server`, `quay.io/ucsc_cgl/redwood-metadata-server`, and `quay.io/ucsc_cgl/redwood-auth-server` docker images locally as appropriate.

In another terminal, test the system (this has to be done from the dcc-ops/redwood directory unless you create your accessToken separately):
```
docker run --rm -it --net=redwood_default --link redwood-nginx:storage.redwood.io --link redwood-nginx:metadata.redwood.io \
    -e ACCESS_TOKEN=$(scripts/createAccessToken.sh) -e REDWOOD_ENDPOINT=redwood.io \
    quay.io/ucsc_cgl/redwood-client:dev bash
$ upload data/someFile
<note the object id outputted>
$ download <objectid> .
```

If that's as expected, you've successfully set up Redwood for development.


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
