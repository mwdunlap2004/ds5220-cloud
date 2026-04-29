from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from chalice import Chalice

app = Chalice(app_name="dp3-wildfire")


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
    resp = _table().query(
        KeyConditionExpression=Key("PK").eq("COUNTRY#CA") & Key("SK").between(f"TS#{start}", f"TS#{now}~"),
        ScanIndexForward=True,
    )
    return resp.get("Items", [])


@app.route("/")
def index():
    return {
        "about": "Tracks active wildfire detections across Canada from NASA FIRMS near-real-time sources.",
        "resources": ["current", "trend", "plot"],
    }


@app.route("/current")
def current():
    items = _query_window(days=1)
    response = {
        "count_24h": len(items),
        "latest": None,
    }
    if items:
        latest = items[-1]
        response["latest"] = {
            "latitude": _to_float(latest.get("latitude")),
            "longitude": _to_float(latest.get("longitude")),
            "confidence": int(latest.get("confidence", 0)),
            "source": latest.get("source"),
            "acq_date": latest.get("acq_date"),
            "acq_time": latest.get("acq_time"),
        }
    return {"response": response}


@app.route("/trend")
def trend():
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

    return {
        "response": {
            "window_days": days,
            "previous_count": first_count,
            "recent_count": second_count,
            "delta": delta,
            "pct_change": pct,
            "escalating": delta > 0,
        }
    }


@app.route("/plot")
def plot():
    bucket = os.environ["PLOT_BUCKET"]
    region = os.environ.get("AWS_REGION", "us-east-1")
    key = os.environ.get("PLOT_KEY", "latest/wildfire_latest.png")
    url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
    return {"response": url}
