#!/bin/bash
if [ ! -f /tmp/newfolder/main.tf ]; then
   mkdir /tmp/newfolder/
   cp -r . /tmp/newfolder/
   cd /tmp/newfolder/
   rm -rf .terraform
   rm -f .terraform.lock.hcl
   rm ./zzz_*
   rm main.tf
   mv main_local_backend main.tf
   terraform init
   terraform apply -auto-approve
fi
