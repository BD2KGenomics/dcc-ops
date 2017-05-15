#!/bin/bash

#cron -f -L 15 && echo "Cron Job set"

java -cp consonance-arch-*.jar io.consonance.arch.containerProvisioner.ContainerProvisionerThreads --config config --endless | tee /consonance_logs/container_provisioner_nohup.out
