#!/bin/bash
if [ ! -d /tmp/newfolder ]; then
   mkdir /tmp/newfolder/
   cp -r . /tmp/newfolder/
   cd /tmp/newfolder/
   rm -rf .terraform
   rm -f .terraform.lock.hcl
   rm ./zzz_*
   if [ -f template_s3_bucket ]; then
      mv template_s3_bucket template_s3_bucket.tf
   fi
   if [ -f template_instance003 ]; then
      mv template_instance003 template_instance003.tf
   fi
   if [ -f provider ]; then
      mv provider provider.tf
   fi
   $HOME/bin/terraform init
   $HOME/bin/terraform apply -auto-approve -var-file=$HOME/terraform.tfvars
   rm -rf /tmp/newfolder
fi
