# Redwood Prod Ops
Admin Guide

## Automated Backups
Daily metadata database backups to s3 can be scheduled with the following command on the metadata database host. This uses [this](https://github.com/agmangas/mongo-backup-s3/) docker image.

You'll have to substitute in your AWS access key id and secret key.

```
docker run --net storageservice_default --link ucsc-metadata-db:mongo -d -e MONGO_HOST=mongo -e MONGO_DB=dcc-metadata -e S3_BUCKET=redwood-backups -e AWS_ACCESS_KEY_ID=123 -e AWS_SECRET_ACCESS_KEY=123 -e BACKUP_INTERVAL=1 -e FILE_PREFIX=metadata-backup- --name metadata-backup agmangas/mongo-backup-s3
```

Daily auth database backups to s3 can be schedule with the following command on the auth database host. This uses [this]() docker image.

Again, you'll have to substitute in your AWS access key id and secret key.

```
docker run --net storageservice_default --link ucsc-auth-db:db -e SCHEDULE="@daily" -e S3_ACCESS_KEY_ID=123 -e S3_SECRET_ACCESS_KEY=123 -e S3_BUCKET=redwood-backups -e S3_PREFIX=auth-backup -e POSTGRES_DATABASE=dcc -e POSTGRES_USER=dcc_auth -e POSTGRES_PASSWORD=pass -e POSTGRES_HOST=db -d schickling/postgres-backup-s3
```
