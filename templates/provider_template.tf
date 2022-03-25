
variable "$access_key_variable" {}

variable "$secret_key_variable" {}

provider "aws" {
  region = "us-east-1"
  # credentials
  access_key = var.$access_key_variable
  secret_key = var.$secret_key_variable
}