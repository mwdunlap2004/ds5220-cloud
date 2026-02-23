# Root module: wires together networking, IAM, compute, and storage.

module "networking" {
  source = "./modules/networking"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  allowed_ssh_cidrs  = var.allowed_ssh_cidrs
  availability_zones = var.availability_zones
}

module "iam" {
  source = "./modules/iam"

  project_name = var.project_name
  environment  = var.environment
  bucket_arn   = module.storage.bucket_arn
}

module "compute" {
  source = "./modules/compute"

  project_name        = var.project_name
  environment         = var.environment
  instance_type       = var.instance_type
  key_name            = var.key_name
  subnet_id           = module.networking.public_subnet_ids[0]
  security_group_ids  = [module.networking.instance_security_group_id]
  iam_instance_profile = module.iam.instance_profile_name
}

module "storage" {
  source = "./modules/storage"

  project_name = var.project_name
  environment  = var.environment
  bucket_name  = var.bucket_name
}
