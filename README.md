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

These directions below assume you are using AWS.  We will include additional cloud instructions as `dcc-ops` matures.

### Collecting Information

Make sure you have:

* your AWS key/secret key
* you know what region you're running in e.g. `us-west-2`

### Starting an AWS VM

Use the AWS console or command line tool to create a host. For example:

* Ubuntu Server 16.04
* r4.large
* 250GB disk

You should make a note of your security group name and ID and ensure you can connect via ssh.

### AWS Tasks

Make sure you do the following:

* assign an Elastic IP (a static IP address) to your instance
* open inbound ports on your security group
    * 80 <- world
    * 8080 <- world
    * 22 <- world
    * 443 <- world
    * all TCP <- the elastic IP of the VM (Make sure you add /32 to the Elastic IP)
    * all TCP <- the security group itself

### Setup for Redwood

Here is a summary of what you need to do. See the Redwood [README](redwood/README.md) for details.

#### Re-route Service Endpoints
Redwood exposes storage, metadata, auth services. Each of these should be made subdomains of your "base domain".
* Make sure you have a domain name associated with your Elastic IP ('example.com')
* Have the subdomains 'auth', 'metadata', and 'storage' point to the same Elastic IP ('auth.example.com', 'metadata.example.com', and 'storage.example.com' and 'example.com' all resolve to the same Elastic IP)

#### Make your S3 Bucket
* On the AWS console, go to S3 and create a bucket.
* Assign it a name. Keep note of the name given to it.
* Get the S3 endpoint. It dependent on your region. See [here](http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region) for the list.

#### Create an AWS IAM Encryption Key
* Go [here](http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html) and follow the instruction for making an AWS IAM Encryption key. Make sure you create it in same region where you created your VM!
* Take note of the AWS IAM Encryption Key ID. You can find it in the AWS console > Services > IAM > Encryption Keys > [your key's details page] > ARN. It is the last part of the ARN (e.g. _arn:aws:kms:us-east-1:862902209576:key/_*0aaad33b-7ead-44be-a56e-3d00c8777042*

Now we're ready to install Redwood.

### Setup for Consonance

You probably want to install the Consonance command line on the VM above so you can submit work.

Download the command line from:

https://github.com/Consonance/consonance/releases

### Setup for Boardwalk

Here is a summary of what you need to do. See the Boardwalk [README](boardwalk/README.md) for details.

#### Create a Google Oauth2 app
* Follow the instructions on [here](http://bitwiser.in/2015/09/09/add-google-login-in-flask.html#creating-a-google-project) under "Creating A Google Project". This will create your Google Oauth2 app, and will provide you with the Google Client ID and the Google Client Secret which you will require for the boardwalk installation. 

### Running the Installer

Once the above setup is done, clone this repository onto your server and run the bootstrap script

    git clone https://github.com/BD2KGenomics/dcc-ops.git && cd dcc-ops && bash install_bootstrap

It will ask you to configure each service.
* Consonance
* Redwood
  * Install in prod mode
  * If the base URL is _example.com_, then _storage.example.com_, _metadata.example.com_, _auth.example.com_, and _<dashboard_vhost>.example.com_ should resolve via DNS to your server.
  * Enter your AWS Key and Secret Key when requested. Redwood will use these to sign requests for upload and download to your S3 bucket
  * On question 'What is your AWS S3 bucket?', put the name of the s3 bucket you created for Redwood.
  * On question 'What is your AWS S3 endpoint?', put the S3 endpoint pertaining to your region. See [here](http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region).
  * On question 'What is your AWS IAM KMS key ID?', put your encryption key ID (See 'Create an AWS IAM Encryption Key" above). If you don't want server-side encryption, you can leave this blank.
* Boardwalk
  * Install in dev mode
  * On question `What is your Google Client ID?`, put your Google Client ID. See [here](http://bitwiser.in/2015/09/09/add-google-login-in-flask.html#creating-a-google-project)
  * On question `What is your Google Client Secret?`, put your Google Client Secret. See [here](http://bitwiser.in/2015/09/09/add-google-login-in-flask.html#creating-a-google-project)
  * On question `What is your DCC Dashboard Host?`, put the domain name resolving to your Virtual Machine (e.g. `example.com`)
  * On question `What is the user and group that should own the files from the metadata-indexer?`, type the `USER:GROUP` pair you want the files downloaded by the indexer to be owned by. The question will show the current `USER:GROUP` pair for the current home directory. Highly recommended to type the same value in there (e.g. `1000:1000`)
  * On question `How should the database for billing should be called?`, type the name to be assigned to the billing database.
  * On question `What should the username be for the billing database?`, type the username for the billing database.
  * On question `What should the username password be for the billing database?`, type some password for the billing database. 
  * On question `What is the AWS profile?`, type some random string (DEV)
  * On question `What is the AWS Access key ID?`, type some random string (DEV)
  * On question `What is the AWS secret access key?`, type some random string (DEV)
  * On question `What is the Luigi Server?`, type some random string (DEV)
  * On question `What is the Postgres Database name for the action service?`, type the name to be assigned to the action service database.
  * On question `What is the Postgres Database user for the action service?`, type the username to be assigned to the the action service database.
  * On question `What is the Postgres Database password for the action service?`, type the password to be assigned to the action service database. 
  
* Common
  * Installing in `dev`mode will use letsencrypt's staging service, which won't exhaust your certificate's limit, but will install fake ssl certificates. `prod` mode will install official SSL certificates.  

Once the installer completes, the system should be up and running. Congratulations! See `docker ps` to get an idea of what's running.

## After Installation

### Confirm Proper Function

To test that everything installed successfully, you can run `cd test && ./integration.sh`. This will do an upload and download with core-client and check the results.

### Upload and Download

End users should be directed to use the [quay.io/ucsc_cgl/core-client](https://quay.io/repository/ucsc_cgl/core-client)
docker image as documented in its [README](https://github.com/BD2KGenomics/dcc-spinnaker-client/blob/develop/README.md).
The `test/integration.sh` file also demonstrates normal core-client usage.

### Troubleshooting

If something goes wrong, you can [open an issue](https://github.com/BD2KGenomics/dcc-ops/issues/new) or [contact a human](https://github.com/BD2KGenomics/dcc-ops/graphs/contributors).

### Tips

* This [blog post](https://www.digitalocean.com/community/tutorials/how-to-remove-docker-images-containers-and-volumes) is helpful if you want to clean up previous images/containers/volumes.

### To Do

* should use a reference rather than checkin the consonance directory, that ends up creating duplication which is not desirable
* the bootstrapper should install Java, Dockstore CLI, and the Consonance CLI
