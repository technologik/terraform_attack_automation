resource "null_resource" "null_tfvars" {
 triggers = {
   tfvars = file("terraform.tfvars")
 }
}

resource "null_resource" "null_envvars" {
  for_each = fileset("/env/", "*")
  triggers = {
    (each.key) = file("/env/${each.key}")
  }
}