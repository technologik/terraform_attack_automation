resource "null_resource" "null_tfvars" {
 triggers = {
   tfvars = file("~/terraform.tfvars")
 }
}

# Hashicorp removed this folder at some point in 2022
#resource "null_resource" "null_envvars" {
#  for_each = fileset("/env/", "*")
#  triggers = {
#    (each.key) = file("/env/${each.key}")
#  }
#}

resource "null_resource" "null_envvars" {
 triggers = {
   tfvars = file("/proc/self/environ")
 }
}