from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from chalice import Chalice

app = Chalice(app_name="dp3-wildfire")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


ddb = boto3.resource("dynamodb")


def _table():
    return ddb.Table(os.environ["DDB_TABLE_NAME"])


def _to_float(v):
    if isinstance(v, Decimal):
        return float(v)
    return v


def _query_window(days: int) -> list[dict]:
    now = int(datetime.now(timezone.utc).timestamp())
    start = now - (days * 86400)
    try:
        resp = _table().query(
            KeyConditionExpression=Key("PK").eq("COUNTRY#CA") & Key("SK").between(f"TS#{start}", f"TS#{now}~"),
            ScanIndexForward=True,
        )
        items = resp.get("Items", [])
        logger.info("Queried items=%s window_days=%s", len(items), days)
        return items
    except Exception as exc:
        logger.exception("Failed querying DynamoDB for window_days=%s: %s", days, exc)
        raise


@app.route("/")
def index():
    return {
        "about": "Tracks active wildfire detections across Canada from NASA FIRMS near-real-time sources.",
        "resources": ["current", "trend", "plot", "map"],
    }


@app.route("/current")
def current():
    try:
        items = _query_window(days=1)
        response = "No wildfire detections in the last 24 hours."
        if items:
            latest = items[-1]
            response = (
                f"Last 24h detections: {len(items)}. "
                f"Latest fire: ({_to_float(latest.get('latitude'))}, {_to_float(latest.get('longitude'))}), "
                f"confidence {int(latest.get('confidence', 0))}, source {latest.get('source')}, "
                f"acquired {latest.get('acq_date')} {latest.get('acq_time')} UTC."
            )
        return {"response": response}
    except Exception as exc:
        logger.exception("current endpoint failed: %s", exc)
        return {"response": {"error": "current_failed", "message": str(exc)}}


@app.route("/trend")
def trend():
    try:
        days = int(app.current_request.query_params.get("days", "7")) if app.current_request.query_params else 7
        days = max(2, min(days, 30))

        recent = _query_window(days=days)
        half = max(1, days // 2)
        first = _query_window(days=days)[: max(1, len(recent) // 2)]
        second = _query_window(days=half)

        first_count = len(first)
        second_count = len(second)
        delta = second_count - first_count
        pct = (delta / first_count * 100.0) if first_count > 0 else None

        pct_text = f"{pct:.1f}%" if pct is not None else "n/a"
        direction = "increasing" if delta > 0 else ("decreasing" if delta < 0 else "flat")
        return {
            "response": (
                f"{days}-day trend: previous window={first_count}, recent window={second_count}, "
                f"delta={delta} ({pct_text}), trend is {direction}."
            )
        }
    except Exception as exc:
        logger.exception("trend endpoint failed: %s", exc)
        return {"response": {"error": "trend_failed", "message": str(exc)}}


@app.route("/plot")
def plot():
    try:
        bucket = os.environ["PLOT_BUCKET"]
        region = os.environ.get("AWS_REGION", "us-east-1")
        key = os.environ.get("PLOT_KEY", "latest/wildfire_latest.png")
        ts = int(datetime.now(timezone.utc).timestamp())
        url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}?t={ts}"
        return {"response": url}
    except Exception as exc:
        logger.exception("plot endpoint failed: %s", exc)
        return {"response": {"error": "plot_failed", "message": str(exc)}}


@app.route("/map")
def map_plot():
    try:
        bucket = os.environ["PLOT_BUCKET"]
        region = os.environ.get("AWS_REGION", "us-east-1")
        key = os.environ.get("MAP_PLOT_KEY", "latest/wildfire_map_latest.png")
        ts = int(datetime.now(timezone.utc).timestamp())
        url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}?t={ts}"
        return {"response": url}
    except Exception as exc:
        logger.exception("map endpoint failed: %s", exc)
        return {"response": {"error": "map_failed", "message": str(exc)}}
