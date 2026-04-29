from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class FIRMSRecord:
    latitude: float
    longitude: float
    acq_date: str
    acq_time: str
    confidence: int
    frp: Optional[float]
    daynight: str
    source: str


@dataclass(frozen=True)
class PatchRequest:
    latitude: float
    longitude: float
    date: str
    layer: str
    half_size_m: int = 1250
    width: int = 224
    height: int = 224
    image_format: str = "image/jpeg"


@dataclass
class IngestionManifestRecord:
    sample_id: str
    label: str
    split: str
    image_path: str
    source_sensor: str
    acq_date: str
    acq_time: str
    latitude: float
    longitude: float
    confidence: Optional[int]
    frp: Optional[float]
    qa_flags: list[str] = field(default_factory=list)
    ingested_at_utc: str = ""
