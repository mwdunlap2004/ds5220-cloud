# Terraform: DS5220 DP3 Part 1 Infrastructure

This stack deploys the DP3-compliant ingestion backbone:
- EventBridge scheduled rule
- Lambda ingest function
- DynamoDB persistent time-series table
- Public S3 plot bucket/prefix for `/plot` URL

## Build Lambda Package First
From repo root:
```bash
mkdir -p build
zip -r build/ingestion.zip ingestion src
```

## Deploy
```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars and set firms_map_key
terraform init
terraform plan
terraform apply
```

## What you wire into Chalice (Part 2)
After apply, use outputs:
- `dynamodb_table_name`
- `plot_bucket_name`
- `plot_url`

Set those in `api/.chalice/config.json` environment variables.
