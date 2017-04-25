# Boardwalk
The core's file browser.

## Overview
Boardwalk is the core's file browser to display the metadata of files stored in redwood. It relies on two key components:
* The metadata-indexer
* The dashboard-service

The metadata-indexer pulls the metadata information from redwood and creates a donor oriented index. It then uses this index to create a file oriented index. Both of these indexes get loaded into elasticsearch. The dashboard-service then reads from elasticsearch and returns queries that can be used to populate the Boardwalk file browser. 

## Deployment
Deployment is done through the `install_bootstrap` script on the root directory. It will ask you a series of question to collect the information required to install boardwalk and its components.

### Create a Google Oauth2 app

Before proceeding, you must ensure that you have a Google OAuth2 app. Follow the instructions on [here](http://bitwiser.in/2015/09/09/add-google-login-in-flask.html#creating-a-google-project) under "Creating A Google Project". 

If you don't want to enable Login and token retrieval through the portal, you can just put some random string for the Google Client ID and Google Client Secret. 

Here is a summary of what you need to do in order to create a Google OAuth2 app:

* Go to [Google's Developer Console](https://console.developers.google.com/).
* On the upper left side of the screen, click on the drop down button.
* Create a project by clicking on the plus sign on the pop-up window.
* On the next pop up window, add a name for your project. 
* Once you create it, click on the "Credentials" section on the left hand side.
* Click on the "OAuth Consent Screen". Fill out a product name and choose an email for the Google Application. Fill the rest of the entries as you see fit for your purposes, or leave them blank, as they are optional. Save it.
* Go to the "Credentials" tab. Click on the "Create Credentials" drop down menu and choose "OAuth Client ID".
* Choose "Web Application" from the menu. Assign it a name. 
* Under "Authorized JavaScript origins", enter `http://<YOUR_SITE>`. Press Enter. Add a second entry, same as the first one, but use *https* instead of *http*
* Under "Authorized redirect URIs", enter `http://<YOUR_SITE>/gCallback`. Press Enter. Add a second entry, same as the first one, but use *https* instead of *http*
* Click "Create". A pop up window will appear with your Google Client ID and Google Client Secret. Save these. If you lose them, you can always go back to the Google Console, and click on your project; the information will be there. Keep these values stored in a safe location. Treat them as you would treat a credit card number. 

**Please note:** at this point, the dashboard only accepts login from emails with a 'ucsc.edu' domain. In the future, it will support different email domains. 

### Development Mode

The boardwalk installer has the option to install boardwalk and its components in either devevelopment or production mode (dev/prod). If you are installing in production, skip this section and head to **Installation Questions**. Otherwise, keep reading.

To make deployment during development faster, dev mode will assume you have cloned *dcc-dashboard, dcc-dashboard-service, and dcc-metadata-indexer* under *dcc-ops/boardwalk* If you are running dcc-ops in dev mode and you haven't already, clone the repos by running the following from within `dcc-ops/boardwalk`:

```
git clone https://github.com/BD2KGenomics/dcc-dashboard-service.git
git clone https://github.com/BD2KGenomics/dcc-metadata-indexer.git
git clone https://github.com/BD2KGenomics/dcc-dashboard.git
```
Make sure you check the branches you will be doing development on within each of the cloned repos.

Once you run the installer, docker-compose will use dev.yml to set up boardwalk and its components. It will create the Docker images using the Dockerfiles located inside `dcc-dashboard, dcc-dashboard-service, and dcc-metadata-indexer/v2`. 

In addition, installing boardwalk in dev mode will also install kibana under `myexample.com/kibana/` to aid in debugging all things related to elasticsearch, as well as to help in making new queries and aggregations that may be necessary. 

### Installation Questions
* Choose a mode you want to run the installer (prod/dev). 
* On question `What is your Google Client ID?`, put your Google Client ID. See [here](http://bitwiser.in/2015/09/09/add-google-login-in-flask.html#creating-a-google-project)
* On question `What is your Google Client Secret?`, put your Google Client Secret. See [here](http://bitwiser.in/2015/09/09/add-google-login-in-flask.html#creating-a-google-project)
* On question `What is your DCC Dashboard Host?`, put the domain name resolving to your Virtual Machine (e.g. `example.com`)
* On question `What is the user and group that should own the files from the metadata-indexer?`, type the `USER:GROUP` pair you want the files downloaded by the indexer to be owned by. The question will show the current `USER:GROUP` pair for the current home directory. Highly recommended to type the same value in there (e.g. `1000:1000`)
* On question `How should the database for billing should be called?`, type the name to be assigned to the billing database.
* On question `What should the username be for the billing database?`, type the username for the billing database.
* On question `What should the username password be for the billing database?`, type some password for the billing database. 
* On question `What is the AWS profile?`, type some random string (DEV, PROD)
* On question `What is the AWS Access key ID?`, type some random string (DEV, PROD)
* On question `What is the AWS secret access key?`, type some random string (DEV, PROD)
* On question `What is the Consonance Address?`, type some random string (DEV, PROD)
* On question `What is the Consonance Token`, type some random string (DEV, PROD)
* On question `What is the Luigi Server?`, type some random string (DEV, PROD)
* On question `What is the Postgres Database name for the action service?`, type the name to be assigned to the action service database.
* On question `What is the Postgres Database user for the action service?`, type the username to be assigned to the the action service database.
* On question `What is the Postgres Database password for the action service?`, type the password to be assigned to the action service database. 

### Checking Docker Containers

You can check which docker containers are running by doing `sudo docker ps`. If the installation was successful, you should see the following containers running:
```
boardwalk_dcc-metadata-indexer_1
boardwalk_dcc-dashboard-service_1
boardwalk_dcc-dashboard_1
boardwalk_nginx_1
boardwalk_boardwalk_1
elasticsearch1
boardwalk_elasticsearch2_1
boardwalk_db_1
boardwalk-billing
```
