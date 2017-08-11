#!/bin/bash
#we put the logback.xml file in /root; so put that path first so the provisioner
#uses those logging parameters instead of using the ones in consonance-arch-*.jar
#which is in /
#the '/' path is second so that the rest of the code is found in 
#consonance-arch-*.jar
cron -L 15 && echo "Cron Job set"

#for remote debugging
java -agentlib:jdwp=transport=dt_socket,server=y,address=8000,suspend=n  -cp "/root/:./*" io.consonance.arch.containerProvisioner.ContainerProvisionerThreads --config config --endless | tee /consonance_logs/container_provisioner_nohup.out

#regular run command
#java -cp consonance-arch-*.jar io.consonance.arch.containerProvisioner.ContainerProvisionerThreads --config config --endless | tee /consonance_logs/container_provisioner_nohup.out
