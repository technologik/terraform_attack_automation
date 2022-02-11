#!/bin/bash
if [ ! -d /tmp/newfolder ]; then
   mkdir /tmp/newfolder/
   cp -r . /tmp/newfolder/
   cd /tmp/newfolder/
   rm -rf .terraform
   rm -f .terraform.lock.hcl
   rm ./zzz_*
   #rm main.tf
   #mv main_local_backend main.tf
   mv template_instance003 template_instance003.tf
   terraform init
   terraform apply -auto-approve
   rm -rf /tmp/newfolder
fi