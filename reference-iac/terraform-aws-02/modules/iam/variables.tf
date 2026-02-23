variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (e.g. dev, staging, prod)"
  type        = string
}

variable "bucket_arn" {
  description = "ARN of the S3 bucket the instance is allowed to access"
  type        = string
}
