terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Create this bucket + table once, manually or via a bootstrap script,
  # BEFORE running `terraform init` against this backend.
  #   aws s3api create-bucket --bucket <your-unique-bucket-name> --region us-east-1
  #   aws dynamodb create-table --table-name job-tracker-tf-locks \
  #     --attribute-definitions AttributeName=LockID,AttributeType=S \
  #     --key-schema AttributeName=LockID,KeyType=HASH \
  #     --billing-mode PAY_PER_REQUEST
  backend "s3" {
    bucket         = "REPLACE_WITH_YOUR_TF_STATE_BUCKET"
    key            = "job-tracker/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "job-tracker-tf-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "job-application-tracker"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
