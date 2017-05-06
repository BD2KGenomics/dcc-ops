#!/bin/bash

#exit script if we try to use an uninitialized variable.
set -o nounset
#exit the script if any statement returns a non-true return value
set -o errexit

#set up storage information variable in case it is not run from Docker compose
#which will poplulate the variables
#set variables to default values if they are not already set
#http://stackoverflow.com/questions/2013547/assigning-default-values-to-shell-variables-with-a-single-command-in-bash
: ${STORAGE_SERVER:=storage_server}
: ${STORAGE_ACCESS_TOKEN:=storage_token}
: ${ELASTIC_SEARCH_SERVER:=elastic_search_server}
: ${ELASTIC_SEARCH_PORT:=elastic_search_port}
: ${TOUCH_FILE_DIRECTORY:=touch_file_directory}
: ${AWS_REGION:=aws_region}

#crontab does not use the PATH from etc/environment so we have to set our 
#own PATH so the consonance command and other tools can be found
#PATH=/home/ubuntu/bin:/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/usr/lib/jvm/java-8-oracle/bin:/usr/lib/jvm/java-8-oracle/db/bin:/usr/lib/jvm/java-8-oracle/jre/bin

VIRTUAL_ENV_PATH=/home/ubuntu/luigi_decider_runs/luigienv/bin
LUIGI_RUNS_PATH=/home/ubuntu/luigi_decider_runs
DECIDER_SOURCE_PATH=${LUIGI_RUNS_PATH}
LOG_FILE_PATH=/home/ubuntu/logs
mkdir -p ${LOG_FILE_PATH}
sudo chown -R ubuntu:ubuntu ${LOG_FILE_PATH}
touch ${LOG_FILE_PATH}/logfile.txt

echo "Starting decider cron job" > ${LOG_FILE_PATH}/cron_decider_log.txt

echo "getting date" >> ${LOG_FILE_PATH}/cron_decider_log.txt
now=$(date +"%T")

#mkdir -p ${LUIGI_RUNS_PATH}

echo "cd ${LUIGI_RUNS_PATH}" >> ${LOG_FILE_PATH}/cron_decider_log.txt
#Go into the appropriate folder
cd "${LUIGI_RUNS_PATH}"

echo "source ${VIRTUAL_ENV_PATH}/activate" >> ${LOG_FILE_PATH}/cron_decider_log.txt
#for some reason set -o nounset thinks activate is an uninitialized variable so turn nounset off
set +o nounset
#Activate the virtualenv
source "${VIRTUAL_ENV_PATH}"/activate
set -o nounset


#start up the Luigi scheduler daemon in case it is not already running
#so we can monitor job status
#once we do this we don't use the --local-scheduler switch in the 
#Luigi command line
echo "Starting Luigi daemon in the background" >> ${LOG_FILE_PATH}/cron_decider_log.txt
sudo luigid --background

echo "Running Luigi RNA-Seq decider" >> ${LOG_FILE_PATH}/cron_decider_log.txt

# run the decider
#use the '--test-mode' switch to skip running Consonance
#This will be the new run commmand:
PYTHONPATH="${DECIDER_SOURCE_PATH}" luigi --module RNA-Seq RNASeqCoordinator --dockstore-tool-running-dockstore-tool "quay.io/ucsc_cgl/dockstore-tool-runner:1.0.10" --workflow-version "3.2.1-1" --touch-file-bucket ${TOUCH_FILE_DIRECTORY} --redwood-host ${STORAGE_SERVER} --redwood-token ${STORAGE_ACCESS_TOKEN} --es-index-host ${ELASTIC_SEARCH_SERVER} --es-index-port ${ELASTIC_SEARCH_PORT} --vm-region ${AWS_REGION} --tmp-dir /datastore --max-jobs 2  > "${LOG_FILE_PATH}"/cron_log_RNA-Seq_decider_stdout.txt 2> "${LOG_FILE_PATH}"/cron_log_RNA-Seq_decider_stderr.txt

#These are log file messages used for testing: 
'''
echo -e "\n\n"
echo "${now} DEBUG!! run of luigi decider!!!" >> ${LOG_FILE_PATH}/logfile.txt
echo "executing consonance --version test" >> ${LOG_FILE_PATH}/logfile.txt
consonance --version >> ${LOG_FILE_PATH}/logfile.txt

echo "redwood server is ${STORAGE_SERVER}" >> ${LOG_FILE_PATH}/logfile.txt
echo "redwood token is ${STORAGE_ACCESS_TOKEN}" >> ${LOG_FILE_PATH}/logfile.txt

echo "elastic search server is ${ELASTIC_SEARCH_SERVER}" >> ${LOG_FILE_PATH}/logfile.txt
echo "elastic search port is ${ELASTIC_SEARCH_PORT}" >> ${LOG_FILE_PATH}/logfile.txt

echo "touch file directory is ${TOUCH_FILE_DIRECTORY}" >> ${LOG_FILE_PATH}/logfile.txt

echo "executing java -version test" >> ${LOG_FILE_PATH}/logfile.txt
java -version >> ${LOG_FILE_PATH}/logfile.txt 2>&1

echo "executing aws test" >> ${LOG_FILE_PATH}/logfile.txt
aws   >> ${LOG_FILE_PATH}/logfile.txt 2>&1
'''



#for some reason set -o nounset thinks deactivate is an uninitialized variable so turn nounset off
set +o nounset
# deactivate virtualenv
deactivate
set -o nounset

