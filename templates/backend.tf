terraform {
 backend "remote" {
   hostname = "$hostname"
   organization = "$organization"
 
   workspaces {
     name = "$workspace"
   }
 }
}