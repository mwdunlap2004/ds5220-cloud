# DS5220 DP3: Wildfire Tracking (FIRMS)

This repo is structured to satisfy both DP3 parts:

1. **Ingestion Pipeline (Part 1)**
- EventBridge schedule triggers a Lambda ingestion function.
- Lambda fetches NASA FIRMS NRT detections for Canada.
- Filtered records are stored in DynamoDB as timestamped time-series items.
- Lambda regenerates a wildfire trend plot and uploads it to public S3 (`latest/wildfire_latest.png`).

2. **Integration API (Part 2)**
- Chalice app (`api/app.py`) exposes:
  - `GET /`
  - `GET /current`
  - `GET /trend`
  - `GET /plot`
- Response shapes follow the Discord bot contract.

## Repo Layout
- `ingestion/handler.py`: scheduled Lambda ingest + S3 plot write.
- `api/app.py`: Chalice API resources.
- `infra/terraform/`: Part 1 AWS infrastructure as code.
- `src/`: shared FIRMS/geospatial utility code.

## Deploy Part 1 (Terraform)
```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# set firms_map_key and any overrides
terraform init
terraform plan
terraform apply
```

Key outputs:
- `dynamodb_table_name`
- `plot_bucket_name`
- `plot_url`

## Deploy Part 2 (Chalice)
1. Install API deps:
```bash
cd api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
2. Update `api/.chalice/config.json` env vars:
- `DDB_TABLE_NAME` = terraform output `dynamodb_table_name`
- `PLOT_BUCKET` = terraform output `plot_bucket_name`
3. Deploy:
```bash
chalice deploy
```

## Discord API Contract
- `GET /` returns:
```json
{
  "about": "...",
  "resources": ["current", "trend", "plot"]
}
```
- Other resources return:
```json
{"response": ...}
```
