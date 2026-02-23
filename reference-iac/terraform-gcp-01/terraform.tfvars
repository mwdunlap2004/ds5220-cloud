# Copy this file to terraform.tfvars and fill in your values
# terraform.tfvars is loaded automatically by Terraform

project_id    = "sds-project-2025"
region        = "us-central1"
zone          = "us-central1-a"
instance_name = "nem2p-instance"
machine_type  = "e2-micro"
bucket_name   = "nmagee-sds-bucket"

# Restrict these to your IP in production
allowed_ssh_cidrs  = ["0.0.0.0/0"]
allowed_http_cidrs = ["0.0.0.0/0"]
