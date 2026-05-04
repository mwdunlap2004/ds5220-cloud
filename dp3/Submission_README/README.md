# DP3 Submission Write-Up

## Project Overview
This project tracks near-real-time wildfire detections across Canada using NASA FIRMS (VIIRS NRT sources). A scheduled, serverless ingestion pipeline writes timestamped detections into DynamoDB and generates public S3 visualizations. A Chalice API exposes current status, trend summary, and plot URLs for Discord bot integration.

## Requirement Checklist

### Part 1: Ingestion Pipeline (Serverless)
- EventBridge scheduled rule: **Implemented** (`infra/terraform/main.tf`, `aws_cloudwatch_event_rule.ingest_schedule`).
- Lambda ingestion function: **Implemented** (`ingestion/handler.py`, deployed as `dp3-wildfire-ingest`).
- Persistent store: **Implemented** (DynamoDB table `dp3-wildfire-firms` with `PK/SK` + `ttl`).
- Data source changes over time: **Implemented** (FIRMS NRT active fire detections).
- Timestamped records: **Implemented** (`epoch` and timestamped `SK` keys).

### Part 2: Integration API (Chalice)
- API Gateway + Lambda via Chalice: **Implemented** (`api/app.py`).
- Zone apex contract (`GET /`): **Implemented** (`about`, `resources`).
- At least 3 resources (`current`, `trend`, `plot`): **Implemented**.
- Public plot URL resource: **Implemented** (`GET /plot` returns public S3 URL).
- Additional stretch resource: **Implemented** (`GET /map` fire-location map URL).

### Wire Format Compatibility
- `GET /`: returns `{ "about": ..., "resources": [...] }`.
- Other resources: return `{ "response": ... }`.
- Output tested with Discord-style calls.

## Logging and Exception Handling Review

### Ingestion (`ingestion/handler.py`)
- Logging: **Implemented** with `logging` logger and step-level logs:
  - start configuration
  - per-source fetch counts/errors
  - DynamoDB write counts
  - query counts
  - S3 upload success
  - final result summary
- Exception handling: **Implemented**
  - `try/except` around source calls, DDB write, DDB query, final orchestration
  - `logger.exception(...)` in failure paths
  - structured error response body on ingestion failure

### API (`api/app.py`)
- Logging: **Implemented**
  - query counts
  - endpoint-level exception logs
- Exception handling: **Implemented**
  - `try/except` in `current`, `trend`, `plot`, `map`
  - safe JSON response with error message instead of hard crash

## Storage Schema
DynamoDB table: `dp3-wildfire-firms`
- `PK`: `COUNTRY#CA`
- `SK`: `TS#<epoch>#<lat,lon>`
- Attributes: `epoch`, `latitude`, `longitude`, `confidence`, `frp`, `daynight`, `source`, `acq_date`, `acq_time`, `ttl`

## Resource Descriptions
- `GET /current`: human-readable summary of latest 24h detections and most recent point.
- `GET /trend`: human-readable trend summary over a configurable day window.
- `GET /plot`: cache-busted URL to time-series image (detections per ingest run).
- `GET /map`: cache-busted URL to Canada fire-location scatter image.

## Plot Generation Strategy
- Render-on-write pattern (in ingestion Lambda).
- S3 keys:
  - `latest/wildfire_latest.png` (time series)
  - `latest/wildfire_map_latest.png` (spatial distribution)
- API only returns URLs.

## Infrastructure Files
- Terraform (Part 1): `infra/terraform/*.tf`
- Chalice config (Part 2): `api/.chalice/config.json`, `api/.chalice/policy-dev.json`

## Important Deployment Notes
1. Rebuild ingestion Lambda package before `terraform apply`.
2. Redeploy Chalice after API code changes.
3. Ensure `api/.chalice/config.json` has real env vars (no placeholders).

## Known Minor Gap / Recommendation
- Terraform Lambda environment currently does not explicitly set `MAP_PLOT_KEY` (code default works). Optional hardening: add `MAP_PLOT_KEY` under `aws_lambda_function.ingest.environment.variables` for explicit config parity.

## Submission Deliverables Mapping
- Deployed ingestion pipeline: **Yes**.
- Deployed Chalice API with required resources: **Yes**.
- Public plot URL in API resource: **Yes**.
- README with source/cadence/schema/resources: **Yes** (root README + this submission write-up).
