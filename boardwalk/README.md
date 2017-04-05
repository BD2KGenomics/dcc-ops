# Boardwalk
The core's file browser.

## Overview
Boardwalk is the core's file browser to display the metadata of files stored in redwood. It relies on two key components:
* The metadata-indexer
* The dashboard-service

The metadata-indexer pulls the metadata information from redwood and creates a donor oriented index. It then uses this index to create a file oriented index. Both of these indexes get loaded into elasticsearch. The dashboard-service then reads from elasticsearch and returns queries that can be used to populate the Boardwalk file browser. 

## Deployment
Deployment is done through the `install_bootstrap` script on the root directory. Currently, the development version is just available; put `dev` when prompted for which mode to run on.

Before proceeding, you must ensure that you have a Google OAuth2 app. Follow the instructions on [here](http://bitwiser.in/2015/09/09/add-google-login-in-flask.html#creating-a-google-project) under "Creating A Google Project"

You need to collect the following information as well before launching the installation:

* Google Client ID; Go to `https://console.developers.google.com/` and look for your Oauth2 app. 
* Google Client Secret; Go to `https://console.developers.google.com/` and look for your Oauth2 app. 

### Installation Questions
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
