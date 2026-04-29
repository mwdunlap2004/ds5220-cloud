from __future__ import annotations

import csv
import io
import time
from typing import Iterable

import requests

from .types import FIRMSRecord


BASE_URL = "https://firms.modaps.eosdis.nasa.gov/usfs/api/area/csv"


def build_area_url(map_key: str, source: str, area: str, day_range: int) -> str:
    if not map_key:
        raise ValueError("map_key is required")
    if day_range < 1 or day_range > 10:
        raise ValueError("day_range must be in [1, 10]")
    return f"{BASE_URL}/{map_key}/{source}/{area}/{day_range}"


def fetch_csv(url: str, timeout_s: int = 30, retries: int = 3, backoff_s: float = 1.5) -> str:
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=timeout_s)
            if resp.status_code == 429:
                raise RuntimeError("FIRMS rate limit hit (429)")
            resp.raise_for_status()
            return resp.text
        except Exception as err:  # noqa: BLE001
            last_err = err
            if attempt < retries:
                time.sleep(backoff_s * attempt)
    raise RuntimeError(f"failed to fetch FIRMS CSV: {last_err}")


def normalize_confidence(raw: str) -> int:
    s = (raw or "").strip().lower()
    if s in {"l", "low"}:
        return 30
    if s in {"n", "nominal"}:
        return 60
    if s in {"h", "high"}:
        return 90
    try:
        return max(0, min(100, int(float(s))))
    except ValueError as exc:
        raise ValueError(f"invalid confidence value: {raw}") from exc


def parse_records(
    csv_text: str,
    source: str,
    min_confidence: int = 70,
    daytime_only: bool = True,
) -> list[FIRMSRecord]:
    reader = csv.DictReader(io.StringIO(csv_text))
    out: list[FIRMSRecord] = []
    for row in reader:
        confidence = normalize_confidence(row.get("confidence", ""))
        daynight = (row.get("daynight") or "").strip().upper()
        if confidence < min_confidence:
            continue
        if daytime_only and daynight != "D":
            continue

        frp_raw = row.get("frp", "")
        frp = float(frp_raw) if str(frp_raw).strip() else None

        out.append(
            FIRMSRecord(
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                acq_date=str(row["acq_date"]).strip(),
                acq_time=str(row["acq_time"]).strip().zfill(4),
                confidence=confidence,
                frp=frp,
                daynight=daynight,
                source=source,
            )
        )
    return out


def fetch_and_filter(
    map_key: str,
    source: str,
    area: str,
    day_range: int,
    min_confidence: int = 70,
    daytime_only: bool = True,
) -> list[FIRMSRecord]:
    url = build_area_url(map_key, source, area, day_range)
    csv_text = fetch_csv(url)
    return parse_records(csv_text, source=source, min_confidence=min_confidence, daytime_only=daytime_only)


def dedupe_records(records: Iterable[FIRMSRecord]) -> list[FIRMSRecord]:
    seen: set[tuple[float, float, str, str]] = set()
    out: list[FIRMSRecord] = []
    for r in records:
        key = (round(r.latitude, 5), round(r.longitude, 5), r.acq_date, r.acq_time)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out
