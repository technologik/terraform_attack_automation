# This file is for demonstrating that apply_on_plan.sh is possible by generating an S3 bucket
resource "random_string" "random_name" {
  length    = 8
  min_lower = 8
}

resource "aws_s3_bucket_acl" "bucket" {
  bucket = aws_s3_bucket.bucket.id
  acl    = "private"
}

resource "aws_s3_bucket" "bucket" {
  bucket = "remove-this-test-bucket-${random_string.random_name.result}"

  tags = {
    Name        = "Remove-This"
    Environment = "Test-Env"
  }
}