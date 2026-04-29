variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "name" {
  description = "Project name prefix"
  type        = string
  default     = "dp3-wildfire"
}

variable "tags" {
  description = "Tags applied to resources"
  type        = map(string)
  default     = {}
}

variable "schedule_expression" {
  description = "EventBridge schedule expression for ingestion"
  type        = string
  default     = "rate(1 hour)"
}

variable "firms_map_key" {
  description = "NASA FIRMS MAP key"
  type        = string
  sensitive   = true
}

variable "ttl_days" {
  description = "DynamoDB TTL horizon in days"
  type        = number
  default     = 90
}

variable "day_range" {
  description = "FIRMS day range"
  type        = number
  default     = 1
}

variable "min_confidence" {
  description = "Minimum FIRMS confidence"
  type        = number
  default     = 70
}

variable "daytime_only" {
  description = "Whether to keep only daytime detections"
  type        = bool
  default     = true
}

variable "firms_area" {
  description = "FIRMS area bbox west,south,east,north"
  type        = string
  default     = "-141.0,41.6,-52.6,83.1"
}

variable "plot_key" {
  description = "S3 object key for latest plot"
  type        = string
  default     = "latest/wildfire_latest.png"
}

variable "plot_bucket_name" {
  description = "Optional custom S3 bucket name for plot hosting (must be globally unique)"
  type        = string
  default     = ""
}

variable "lambda_zip_path" {
  description = "Path to prebuilt ingestion lambda zip package"
  type        = string
  default     = "../../build/ingestion.zip"
}
