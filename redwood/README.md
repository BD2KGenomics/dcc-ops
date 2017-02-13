# Redwood
Highly Automated Cloud Data Storage

## Overview
Redwood uses the ICGC Storage System to save and track data bundles in Amazon S3 or an S3-compliant data store.
If applicable, server-side encryption is performed behind the scenes, and multipart upload/download are used to improve data transfer times.
Each bundle of files includes a _metadata.json_ file that can be used to trigger analysis or workflow result reporting.

## Run the System for Development
You'll need docker and docker-compose installed.

_Note:_ If you're making changes to the storage system source code you should build the `quay.io/ucsc_cgl/redwood-storage-server`, `quay.io/ucsc_cgl/redwood-metadata-server`, and `quay.io/ucsc_cgl/redwood-auth-server` docker images locally as appropriate.

Start the system with:

```
docker-compose -f base.yml -f dev.yml up
```

_Note:_ A `~/.aws/credentials` file is assumed to exist to exist on the host.


Then create a testing accessToken with

```
scripts/createAccessToken.sh
```

Now you should be able to upload and download files:
```
docker run --rm -it --net=redwood_default --link redwood-nginx:storage.ucsc-cgl.org --link redwood-nginx:metadata.ucsc-cgl.org \
    -e ACCESS_TOKEN=<your_access_token> -e REDWOOD_ENDPOINT=ucsc-cgl.org \
    quay.io/ucsc_cgl/redwood-client:dev bash
$ upload data/someFile
<note the object id outputted>
$ download <objectid> .
```


## Automated Backups
In the past, automatic daily backups were scheduled with the following command on the metadata database host. This uses [this](https://github.com/agmangas/mongo-backup-s3/) docker image.

Soon this will be handled by the production compose file.

```
docker run --net storageservice_default --link ucsc-metadata-db:mongo -d -e MONGO_HOST=mongo -e MONGO_DB=dcc-metadata -e S3_BUCKET=redwood-backups -e AWS_ACCESS_KEY_ID=123 -e AWS_SECRET_ACCESS_KEY=123 -e BACKUP_INTERVAL=1 -e FILE_PREFIX=metadata-backup- --name metadata-backup agmangas/mongo-backup-s3
```

Sim. for the auth database.

```
docker run --net storageservice_default --link ucsc-auth-db:db -e SCHEDULE="@daily" -e S3_ACCESS_KEY_ID=123 -e S3_SECRET_ACCESS_KEY=123 -e S3_BUCKET=redwood-backups -e S3_PREFIX=auth-backup -e POSTGRES_DATABASE=dcc -e POSTGRES_USER=dcc_auth -e POSTGRES_PASSWORD=pass -e POSTGRES_HOST=db -d schickling/postgres-backup-s3
```

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
- URLs _storage.yourdomain.com_ and _metadata.yourdomain.com_ should resolve to your ec2.

Copy or clone this project (_dcc-redwood-compose_) over to the the ec2
- `git clone git@github.com:BD2KGenomics/dcc-redwood-compose.git`

Update _conf/application.storage.properties_
- s3.accessKey: your _redwood_ IAM user's access key
- s3.secretKey: your _redwood_ IAM user's secret key
- s3.masterEncryptionKeyId: the id of your KMS key
- s3.endpoint: the s3 endpoint to use (depends on your s3 bucket region)
- bucket.name.object: your s3 bucket's name
- server.ssl.key-store-password: the password to your server's ssl keystore

Update _.env_
- see inline comments

Run the system
- `docker-compose -f base.yml -f prod.yml up -d`
- You should schedule this command to run on boot as an upstart/systemd job

At this point, Redwood should be up and running.

To confirm this: generate an accessToken with `scripts/createAccessToken.sh` then do a test upload/download from the server:
```
docker run --rm -it --net=redwood_default --link redwood-nginx:storage.ucsc-cgl.org --link redwood-nginx:metadata.ucsc-cgl.org \
    -e ACCESS_TOKEN=<your_access_token> -e REDWOOD_ENDPOINT=ucsc-cgl.org \
    quay.io/ucsc_cgl/redwood-client:dev bash
$ upload data/someFile
<note the object id outputted>
$ download <objectid> .
```

If everything is as expected, congratulations! You've deployed Redwood.
