resource "random_string" "random_name" {
  length    = 8
  min_lower = 8
}

resource "aws_s3_bucket" "bucket" {
  bucket = "remove-this-test-bucket-${random_string.random_name.result}"
  acl    = "private"

  tags = {
    Name        = "Remove-This"
    Environment = "Test-Env"
  }
}