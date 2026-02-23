variable "project_id" {
  description = "The GCP project ID to deploy resources into"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone for the compute instance"
  type        = string
  default     = "us-central1-a"
}

variable "instance_name" {
  description = "Name of the compute instance"
  type        = string
  default     = "nem-instance"
}

variable "machine_type" {
  description = "GCP machine type for the compute instance"
  type        = string
  default     = "e2-micro"
}

variable "image" {
  description = "Boot disk image for the compute instance"
  type        = string
  default     = "debian-cloud/debian-12"
}

variable "bucket_name" {
  description = "Globally unique name for the GCS bucket"
  type        = string
}

variable "allowed_ssh_cidrs" {
  description = "List of CIDR ranges allowed to SSH into the instance"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "allowed_http_cidrs" {
  description = "List of CIDR ranges allowed to reach port 80"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "startup_script" {
  description = "Bash script run when the instance first boots (e.g. install packages, write files)"
  type        = string
  default     = ""
  sensitive   = true
}
