from __future__ import annotations

import io
import json
import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from PIL import Image, ImageDraw

from src.firms_client import dedupe_records, fetch_and_filter


ddb = boto3.resource("dynamodb")
s3 = boto3.client("s3")


def _epoch_now() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _build_item(record, ingested_at: int, ttl_days: int) -> dict:
    pk = f"COUNTRY#CA"
    sk = f"TS#{ingested_at}#{record.latitude:.4f},{record.longitude:.4f}"
    ttl = ingested_at + (ttl_days * 86400)
    return {
        "PK": pk,
        "SK": sk,
        "epoch": ingested_at,
        "latitude": Decimal(str(record.latitude)),
        "longitude": Decimal(str(record.longitude)),
        "confidence": int(record.confidence),
        "frp": Decimal(str(record.frp if record.frp is not None else 0.0)),
        "daynight": record.daynight,
        "source": record.source,
        "acq_date": record.acq_date,
        "acq_time": record.acq_time,
        "ttl": ttl,
    }


def _put_records(table_name: str, records: list, ttl_days: int) -> int:
    table = ddb.Table(table_name)
    ingested_at = _epoch_now()
    count = 0
    with table.batch_writer(overwrite_by_pkeys=["PK", "SK"]) as bw:
        for r in records:
            bw.put_item(Item=_build_item(r, ingested_at, ttl_days))
            count += 1
    return count


def _query_last_days(table_name: str, days: int) -> list[dict]:
    from boto3.dynamodb.conditions import Key

    table = ddb.Table(table_name)
    now = _epoch_now()
    start = now - (days * 86400)

    resp = table.query(
        KeyConditionExpression=Key("PK").eq("COUNTRY#CA") & Key("SK").between(f"TS#{start}", f"TS#{now}~"),
        ScanIndexForward=True,
    )
    return resp.get("Items", [])


def _render_plot(items: list[dict]) -> bytes:
    daily = {}
    for it in items:
        dt = datetime.fromtimestamp(int(it["epoch"]), tz=timezone.utc).strftime("%Y-%m-%d")
        daily[dt] = daily.get(dt, 0) + 1

    xs = sorted(daily.keys())
    ys = [daily[d] for d in xs]
    width, height = 1000, 500
    margin = 60

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # Axes
    draw.line((margin, height - margin, width - margin, height - margin), fill="black", width=2)
    draw.line((margin, margin, margin, height - margin), fill="black", width=2)

    if ys:
        y_max = max(ys) if max(ys) > 0 else 1
        x_span = max(1, len(ys) - 1)
        points = []
        for i, val in enumerate(ys):
            x = margin + int((width - 2 * margin) * (i / x_span))
            y = (height - margin) - int((height - 2 * margin) * (val / y_max))
            points.append((x, y))
        if len(points) == 1:
            draw.ellipse((points[0][0] - 4, points[0][1] - 4, points[0][0] + 4, points[0][1] + 4), fill="red")
        else:
            draw.line(points, fill="red", width=3)
            for px, py in points:
                draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill="red")

    draw.text((margin, 20), "Wildfire Detections (Last 7 Days)", fill="black")

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


def lambda_handler(_event, _context):
    map_key = os.environ["FIRMS_MAP_KEY"]
    table_name = os.environ["DDB_TABLE_NAME"]
    plot_bucket = os.environ["PLOT_BUCKET"]
    plot_key = os.environ.get("PLOT_KEY", "latest/wildfire_latest.png")
    ttl_days = int(os.environ.get("TTL_DAYS", "90"))
    day_range = int(os.environ.get("DAY_RANGE", "1"))
    min_conf = int(os.environ.get("MIN_CONFIDENCE", "70"))
    daytime_only = os.environ.get("DAYTIME_ONLY", "true").lower() == "true"
    area = os.environ.get("FIRMS_AREA", "-141.0,41.6,-52.6,83.1")

    sources = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]
    all_records = []
    for source in sources:
        try:
            recs = fetch_and_filter(
                map_key=map_key,
                source=source,
                area=area,
                day_range=day_range,
                min_confidence=min_conf,
                daytime_only=daytime_only,
            )
            all_records.extend(recs)
        except Exception:
            continue

    records = dedupe_records(all_records)
    inserted = _put_records(table_name, records, ttl_days=ttl_days)

    items = _query_last_days(table_name, days=7)
    if items:
        plot = _render_plot(items)
        s3.put_object(
            Bucket=plot_bucket,
            Key=plot_key,
            Body=plot,
            ContentType="image/png",
        )

    return {
        "statusCode": 200,
        "body": json.dumps({"inserted": inserted, "records_considered": len(records)}),
    }
