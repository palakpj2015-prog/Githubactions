terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

# ---------------------------------------------------------
# ECR REPOSITORY
# ---------------------------------------------------------

# AWS-managed encryption is sufficient for this Free Tier POC.
# A customer-managed KMS key is intentionally not used.
# tfsec:ignore:aws-ecr-repository-customer-key
resource "aws_ecr_repository" "app" {
  name                 = var.project_name
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Purpose = "github-actions-genai-poc"
  }
}

# ---------------------------------------------------------
# S3 ARTIFACT BUCKET
# ---------------------------------------------------------

# Customer-managed KMS encryption and access logging are
# intentionally omitted for this Free Tier POC.
resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.project_name}-artifacts-${data.aws_caller_identity.current.account_id}"

  tags = {
    Purpose = "github-actions-genai-poc"
  }
}

# ---------------------------------------------------------
# S3 VERSIONING
# ---------------------------------------------------------

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ---------------------------------------------------------
# S3 SERVER-SIDE ENCRYPTION
# ---------------------------------------------------------

# tfsec:ignore:aws-s3-encryption-customer-key
resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ---------------------------------------------------------
# S3 PUBLIC ACCESS BLOCK
# ---------------------------------------------------------

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}