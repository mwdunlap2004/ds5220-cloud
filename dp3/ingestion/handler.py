from __future__ import annotations

import io
import json
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from PIL import Image, ImageDraw

from src.firms_client import dedupe_records, fetch_and_filter


ddb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    try:
        table = ddb.Table(table_name)
        ingested_at = _epoch_now()
        count = 0
        with table.batch_writer(overwrite_by_pkeys=["PK", "SK"]) as bw:
            for r in records:
                bw.put_item(Item=_build_item(r, ingested_at, ttl_days))
                count += 1
        logger.info("Wrote %s records to DynamoDB table=%s", count, table_name)
        return count
    except Exception as exc:
        logger.exception("Failed writing records to DynamoDB table=%s: %s", table_name, exc)
        raise


def _query_last_days(table_name: str, days: int) -> list[dict]:
    from boto3.dynamodb.conditions import Key

    table = ddb.Table(table_name)
    now = _epoch_now()
    start = now - (days * 86400)

    try:
        resp = table.query(
            KeyConditionExpression=Key("PK").eq("COUNTRY#CA") & Key("SK").between(f"TS#{start}", f"TS#{now}~"),
            ScanIndexForward=True,
        )
        items = resp.get("Items", [])
        logger.info("Queried %s items from table=%s for days=%s", len(items), table_name, days)
        return items
    except Exception as exc:
        logger.exception("Failed querying table=%s for days=%s: %s", table_name, days, exc)
        raise


def _render_plot(items: list[dict]) -> bytes:
    per_run = {}
    for it in items:
        epoch = int(it["epoch"])
        per_run[epoch] = per_run.get(epoch, 0) + 1

    epochs = sorted(per_run.keys())
    ys = [per_run[e] for e in epochs]
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

    draw.text((margin, 20), "Wildfire Detections Per Ingest Run (Last 7 Days)", fill="black")
    draw.text((width // 2 - 80, height - margin + 20), "X-axis: Ingest Time (UTC)", fill="black")
    draw.text((8, margin - 20), "Y-axis: Detection Count", fill="black")

    # Y-axis ticks (0, mid, max)
    y_max = max(ys) if ys else 1
    for val in sorted({0, max(1, y_max // 2), y_max}):
        y_tick = (height - margin) - int((height - 2 * margin) * (val / max(1, y_max)))
        draw.line((margin - 5, y_tick, margin, y_tick), fill="black", width=1)
        draw.text((10, y_tick - 6), str(val), fill="black")

    # X-axis tick labels at a few points
    if epochs:
        tick_positions = sorted({0, len(epochs) // 2, len(epochs) - 1})
        x_span = max(1, len(epochs) - 1)
        for idx in tick_positions:
            epoch = epochs[idx]
            x = margin + int((width - 2 * margin) * (idx / x_span))
            draw.line((x, height - margin, x, height - margin + 5), fill="black", width=1)
            label = datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%m-%d %H:%M")
            draw.text((x - 35, height - margin + 8), label, fill="black")

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


def _render_canada_fire_map(items: list[dict]) -> bytes:
    # Approximate Canada bounds used in ingestion defaults.
    min_lon, min_lat, max_lon, max_lat = -141.0, 41.6, -52.6, 83.1
    width, height = 1000, 600
    margin = 60

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # Plot frame
    draw.rectangle((margin, margin, width - margin, height - margin), outline="black", width=2)
    draw.text((margin, 20), "Detected Fire Locations (Canada, Last 7 Days)", fill="black")
    draw.text((width // 2 - 90, height - margin + 20), "Longitude", fill="black")
    draw.text((10, margin - 20), "Latitude", fill="black")

    x_span = max_lon - min_lon
    y_span = max_lat - min_lat

    # Axis ticks (coarse, readable)
    lon_ticks = [-140, -120, -100, -80, -60]
    lat_ticks = [45, 55, 65, 75, 83]
    for lon in lon_ticks:
        x = margin + int((width - 2 * margin) * ((lon - min_lon) / x_span))
        draw.line((x, height - margin, x, height - margin + 6), fill="black", width=1)
        draw.text((x - 14, height - margin + 8), str(lon), fill="black")
    for lat in lat_ticks:
        y = (height - margin) - int((height - 2 * margin) * ((lat - min_lat) / y_span))
        draw.line((margin - 6, y, margin, y), fill="black", width=1)
        draw.text((12, y - 6), str(lat), fill="black")

    # Plot points
    for it in items:
        lat = float(it.get("latitude", 0))
        lon = float(it.get("longitude", 0))
        if lon < min_lon or lon > max_lon or lat < min_lat or lat > max_lat:
            continue
        x = margin + int((width - 2 * margin) * ((lon - min_lon) / x_span))
        y = (height - margin) - int((height - 2 * margin) * ((lat - min_lat) / y_span))
        draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill="red")

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


def lambda_handler(_event, _context):
    map_key = os.environ["FIRMS_MAP_KEY"]
    table_name = os.environ["DDB_TABLE_NAME"]
    plot_bucket = os.environ["PLOT_BUCKET"]
    plot_key = os.environ.get("PLOT_KEY", "latest/wildfire_latest.png")
    map_plot_key = os.environ.get("MAP_PLOT_KEY", "latest/wildfire_map_latest.png")
    ttl_days = int(os.environ.get("TTL_DAYS", "90"))
    day_range = int(os.environ.get("DAY_RANGE", "1"))
    min_conf = int(os.environ.get("MIN_CONFIDENCE", "70"))
    daytime_only = os.environ.get("DAYTIME_ONLY", "true").lower() == "true"
    area = os.environ.get("FIRMS_AREA", "-141.0,41.6,-52.6,83.1")
    logger.info(
        "Ingest start table=%s bucket=%s area=%s day_range=%s min_conf=%s daytime_only=%s",
        table_name,
        plot_bucket,
        area,
        day_range,
        min_conf,
        daytime_only,
    )

    sources = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]
    all_records = []
    source_stats = {}
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
            source_stats[source] = {"status": "ok", "count": len(recs)}
            logger.info("Fetched source=%s count=%s", source, len(recs))
        except Exception as exc:
            source_stats[source] = {"status": "error", "error": str(exc)}
            logger.exception("Failed fetch source=%s: %s", source, exc)
            continue

    try:
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
            logger.info("Uploaded plot bucket=%s key=%s bytes=%s", plot_bucket, plot_key, len(plot))
            map_plot = _render_canada_fire_map(items)
            s3.put_object(
                Bucket=plot_bucket,
                Key=map_plot_key,
                Body=map_plot,
                ContentType="image/png",
            )
            logger.info("Uploaded map plot bucket=%s key=%s bytes=%s", plot_bucket, map_plot_key, len(map_plot))
        else:
            logger.warning("No items available for plot generation in last 7 days")

        result = {
            "inserted": inserted,
            "records_considered": len(records),
            "source_stats": source_stats,
        }
        logger.info("Ingest complete result=%s", result)
        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as exc:
        logger.exception("Ingest failed: %s", exc)
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": "ingestion_failed",
                    "message": str(exc),
                    "source_stats": source_stats,
                }
            ),
        }
