from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from .types import FIRMSRecord


@dataclass(frozen=True)
class SamplePoint:
    latitude: float
    longitude: float
    label: str
    acq_date: str
    acq_time: str


def positive_samples(records: list[FIRMSRecord]) -> list[SamplePoint]:
    return [
        SamplePoint(
            latitude=r.latitude,
            longitude=r.longitude,
            label="wildfire",
            acq_date=r.acq_date,
            acq_time=r.acq_time,
        )
        for r in records
    ]


def spatial_buffer_negatives(
    records: list[FIRMSRecord],
    lat_jitter_deg: float = 0.7,
    lon_jitter_deg: float = 0.7,
    seed: int = 42,
) -> list[SamplePoint]:
    rng = random.Random(seed)
    out: list[SamplePoint] = []
    for r in records:
        lat = max(-89.9, min(89.9, r.latitude + rng.choice([-1, 1]) * lat_jitter_deg))
        lon = r.longitude + rng.choice([-1, 1]) * lon_jitter_deg
        if lon > 180:
            lon -= 360
        if lon < -180:
            lon += 360
        out.append(
            SamplePoint(
                latitude=lat,
                longitude=lon,
                label="nowildfire",
                acq_date=r.acq_date,
                acq_time=r.acq_time,
            )
        )
    return out


def temporal_displacement_negatives(records: list[FIRMSRecord], days_offset: int = 180) -> list[SamplePoint]:
    out: list[SamplePoint] = []
    for r in records:
        dt = datetime.strptime(r.acq_date, "%Y-%m-%d")
        shifted = (dt - timedelta(days=days_offset)).strftime("%Y-%m-%d")
        out.append(
            SamplePoint(
                latitude=r.latitude,
                longitude=r.longitude,
                label="nowildfire",
                acq_date=shifted,
                acq_time=r.acq_time,
            )
        )
    return out


def hotspot_exclusion_filter(
    candidates: list[SamplePoint],
    hotspots: list[FIRMSRecord],
    proximity_deg: float = 0.05,
) -> list[SamplePoint]:
    hotspot_coords = [(h.latitude, h.longitude) for h in hotspots]
    out: list[SamplePoint] = []
    for c in candidates:
        keep = True
        for hlat, hlon in hotspot_coords:
            if abs(c.latitude - hlat) <= proximity_deg and abs(c.longitude - hlon) <= proximity_deg:
                keep = False
                break
        if keep:
            out.append(c)
    return out


def build_negative_samples(
    records: list[FIRMSRecord],
    strategies: list[str],
    seed: int = 42,
) -> list[SamplePoint]:
    pool: list[SamplePoint] = []
    if "spatial_buffer" in strategies:
        pool.extend(spatial_buffer_negatives(records, seed=seed))
    if "temporal_displacement" in strategies:
        pool.extend(temporal_displacement_negatives(records))
    if "hotspot_exclusion" in strategies:
        pool = hotspot_exclusion_filter(pool, records)

    deduped: dict[tuple[float, float, str, str], SamplePoint] = {}
    for s in pool:
        key = (round(s.latitude, 5), round(s.longitude, 5), s.acq_date, s.acq_time)
        deduped[key] = s
    return list(deduped.values())


def train_valid_test_split(items: list[SamplePoint], ratios: tuple[float, float, float] = (0.7, 0.15, 0.15)) -> dict[str, list[SamplePoint]]:
    if len(ratios) != 3 or abs(sum(ratios) - 1.0) > 1e-6:
        raise ValueError("ratios must sum to 1.0")

    n = len(items)
    n_train = int(n * ratios[0])
    n_valid = int(n * ratios[1])
    train = items[:n_train]
    valid = items[n_train : n_train + n_valid]
    test = items[n_train + n_valid :]
    return {"train": train, "valid": valid, "test": test}
