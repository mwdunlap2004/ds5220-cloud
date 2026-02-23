output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "instance_id" {
  description = "ID of the EC2 instance"
  value       = module.compute.instance_id
}

output "instance_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = module.compute.instance_public_ip
}

output "bucket_id" {
  description = "ID of the S3 bucket"
  value       = module.storage.bucket_id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.storage.bucket_arn
}
