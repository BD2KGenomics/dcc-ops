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
* you know what region your running in e.g. `us-west-2`

### Starting an AWS VM

Use the AWS console or command line tool to create a host, I chose:

* Ubuntu Server 16.04
* r4.large
* 250GB disk
* make a note of your security group name and ID
* your pem key installed somewhere on this box

### AWS Tasks

Make sure you do the following:

* assign an Elastic IP (a static IP address) to your instance
* open inbound ports on your security group
    * 80 <- world
    * 8080 <- world
    * 22 <- world
    * 443 <- world
    * 8444 <- world (Redwood)
    * 5000 <- world (Redwood)
    * 5431 <- world (Redwood)
    * 8443 <- world (Redwood)
    * 9443 <- world (Redwood)
    * all TCP <- the elastic IP of the VM (Make sure you add /32 to the Elastic IP)
    * all TCP <- the security group itself

### Setup for Redwood (Dev Mode)

See [README](redwood/README.md) for various tasks that need to be done before running the install_bootstrap script for this system.

Here is a summary of what you need to do:

#### Re-route Subdomains
* Make sure you have a domain name associated with your Elastic IP ('example.com')
* Have the subdomains 'auth', 'metadata', and 'storage' point to the same Elastic IP ('auth.example.com', 'metadata.example.com', and 'storage.example.com' and 'example.com' all resolve to the same Elastic IP)

#### Make your S3 Bucket
* On the AWS console, log go to S3.
* Click on create Bucket.
* Assign it a name. Keep note of the name given to it.
* Get the S3 endpoint. It dependent on your region. See [here](http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region) for the list.
* Make a folder called 'data' within your S3 bucket.
* Within 'data', upload an empty file called 'heliograph'.

#### Create an AWS IAM Encryption Key
* Go [here](http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html) and follow the instruction for making an AWS IAM Encryption key. Make sure you create them using the same region where you created your VM!
* Take note of the AWS IAM Encryption Key ID. You can find it in the AWS console by going to [here](https://console.aws.amazon.com/iam/home#/encryptionKeys/).

#### Get your AWS Access Key and AWS Secret Key
* You can obtain your AWS access and secret key if you don't have a pair by clicking "Services" > "Security, Identity & Compliance" > "IAM".
* On the left side, click on Users. Select your user.
* Select the "Security Credentials" tab. Under the "Access Keys" section, click on "Create access key".
* Keep the key pair in a secure location, as this is sensitive information.

Now that you have the required components and information, let's go ahead and do the actual installation.

#### Installing Redwood Via the bootsrap
* First, clone this repo to the VM you just created (`git clone https://github.com/BD2KGenomics/dcc-ops.git`)
* `cd` inside `dcc-ops` and run `bash install_bootstrap`
* Follow the initial bootstraper instructions. These will install some packages. It will also ask you to install docker and docker-compose in case you don't have them installed in your VM.
* Install redwood in dev mode.
* On question 'What is your AWS Key?', put your AWS Access Key
* On question 'What is your AWS Secret Key?', put your AWS Secret Key
* On question 'What is your AWS S3 bucket?', put your S3 bucket name
* On question 'What is your AWS S3 endpoint?', put the S3 endpoint pertaining to your region. See [here](http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region).
* On question 'What is your AWS AIM KMS key ID?', put your AIM KMS key ID generated (See the 'Create an AWS IAM Encryption Key" section above).

#### Sample Upload and Download
* From within `dcc-ops`, you can create a token to download and upload by doing `sudo redwood/scripts/createAccessToken.sh`. Take note of your token, as it will be used for uploading and downloading.
* In your home directory, do `git clone https://github.com/BD2KGenomics/dcc-spinnaker-client.git`, and in the cloned repo, do `git checkout feature/redwood_scoped_auth`. This branch will contain some sample files and manifests that we can use for upload and download.
* To do a sample upload, run the command below (remember to substitute your token!):

```
sudo docker run --rm --net=redwood_default -it --link redwood-nginx:metadata.redwood.io --link redwood-nginx:storage.redwood.io -e ACCESS_TOKEN=<GENERATED_TOKEN> -v $(pwd)/manifests:/manifests -v $(pwd)/samples:/samples -v $(pwd)/outputs:/outputs quay.io/ucsc_cgl/core-client:experimental --force-upload /manifests/two_manifest.tsv
```
This command will upload the files specified in the manifest file (`two_manifest.tsv` in this case). Look at the receipt file within `outputs/` and get one of the file UUIDs so you can try and do a download.

* To do a sample download, run the command below (remember to substitute your token and a file uuid!):

```
sudo docker run --rm -it --net=redwood_default --link redwood-nginx:storage.redwood.io --link redwood-nginx:metadata.redwood.io -e ACCESS_TOKEN=<GENERATED_TOKEN> -e REDWOOD_ENDPOINT=redwood.io -v `pwd`/outputs2:/outputs quay.io/ucsc_cgl/redwood-client:1.1.1 download <FILE_UUID> /outputs
```
This command will download the file associated with the file uuid. You can find it inside `outputs2/<bundle_uuid>/`. 

### Setup for Consonance

You probably want to install the Consonance command line on the VM above so you can submit work.

Download the command line from:

https://github.com/Consonance/consonance/releases

### Running the Bootstrap Script

    curl -L https://<url>/install_bootstrap | bash

Until we get a URL to host this one you just do:

    bash install_bootstrap

On the AWS VM.  It will ask you to configure each service.

### Cleaning up Docker Images/Containers/Volumes

This [blog post](https://www.digitalocean.com/community/tutorials/how-to-remove-docker-images-containers-and-volumes) is helpful if you want to clean up previous images/containers/volumes.

## TODO

* should use a reference rather than checkin the consonance directory, that ends up creating duplication which is not desirable
* the bootstrapper should install Java, Dockstore CLI, and the Consonance CLI
