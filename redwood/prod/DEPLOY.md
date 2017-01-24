# Deploy Guide
This is a guide for deploying Redwood to production on AWS.

_Note:_ Create bucket, ec2, encryption key, etc. in the same region.
- Region: Oregon (us-west-2)

Create the storage system S3 bucket (with logging enabled). This will hold all the storage system data.
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

Create the storage service EC2.
- AMI: Amazon Linux AMI 2016.09.0 (PV) - ami-3c3b632b
- Instance Type: m4.xlarge
- IAM Role: redwood-2.0.1-server
- Security Group Name: redwood-2.0.1-security-group
- SSH Key Pair: <your key pair>

Set up the server's security group (_redwood-server_)
- set it to reject all incoming requests except your ssh for now

Connect to the EC2.
- `ssh ec2-user@35.162.230.56`

Prepare the system.
- `mkdir -p ~/redwood/dcc-auth && mkdir ~/redwood/dcc-metadata && mkdir ~/redwood/dcc-storage`
- add `export DCC_HOME=~/redwood` to your ~/.bash_profile (and `source ~/.bash_profile`).
- install docker and docker-compose

Create an ACM (Amazon Certificate Manager) ssl certificate for your desired redwood endpoint.
- e.g. _storage.ucsc-cgl.org_
  - adding a wildcard SAN like _*.ucsc-cgl.org_ is recommended

Create load balancer target groups for storage, metadata, and auth servers.
- redwood-storage-server target group
  - port 5431
  - add the ec2 as an instance
- redwood-metadata-server target group
  - port 8444
  - add the ec2 as an instance
- redwood-auth-server target group
  - port 8443
  - add the ec2 as an instance

Create the load balancer
- internet-facing
- application elb
- use https with the new ACM certificate on the load balancer frontend
- use https on the backend
- set up 3 listeners
  - route elb port 5431 to the redwood-storage-server target group
  - route elb port 8444 to the redwood-metadata-server target group
  - route elb port 8443 to the redwood-auth-server target group
- set up the security group (_redwood-balancer_)
  - traffic to elb port 5431 should be allowed from anywhere
  - traffic to elb port 8444 should be allowed from anywhere
  - traffic to elb port 8443 should be restricted to the redwood servers' security group

Update your server instance security group _redwood-server_
- allow traffic to port 5431, 8444, and 8443 from only the _redwood-balancer_ security group
- leave everything else restricted

Point your domain to your load balancer
- point your domain to an AWS Route53 hosted zone
- add a record set as follows in that hosted zone
  - Type: A - IPv4
  - Alias: Yes
  - Alias Target: redwood elb

Locally build the _dcc-auth_, _dcc-metadata_, and _dcc-storage_ projects into their respective _*-dist.tar.gz_ files
- see this project's _README.md_

Copy and extract these archives to the ec2, then build the docker images of each of these
- see this project's _README.md_

Copy or clone this project (_dcc-redwood-compose_) over to the the ec2
- `git clone git@github.com:BD2KGenomics/dcc-redwood-compose.git`

Update _conf/application.storage.properties_
- s3.accessKey: your _redwood_ IAM user's access key
- s3.secretKey: your _redwood_ IAM user's secret key
- s3.masterEncryptionKeyId: the id of your KMS key
- s3.endpoint: the s3 endpoint to use (depends on your s3 bucket region)
- bucket.name.object: your s3 bucket's name
- server.ssl.key-store-password: the password to your server's ssl keystore

Run the system
- `docker-compose up -d`

You're done! At this point you should be able to upload and download data from redwood.
