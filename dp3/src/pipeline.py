from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .firms_client import dedupe_records, fetch_and_filter
from .geo import build_square_bbox
from .gibs_client import build_getmap_url, fetch_patch_bytes
from .preprocess import is_visually_valid, standardize_image
from .sampler import SamplePoint, build_negative_samples, positive_samples, train_valid_test_split
from .types import FIRMSRecord, IngestionManifestRecord, PatchRequest


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def default_filename(lon: float, lat: float, acq_date: str, acq_time: str) -> str:
    return f"{lon:.5f},{lat:.5f}_{acq_date}_{acq_time}.jpg"


def save_sample(
    sample: SamplePoint,
    split: str,
    output_root: Path,
    image_bytes: bytes,
    source_sensor: str,
    confidence: int | None = None,
    frp: float | None = None,
    min_non_black_ratio: float = 0.02,
) -> IngestionManifestRecord | None:
    image = standardize_image(image_bytes)
    if not is_visually_valid(image, min_non_black_ratio=min_non_black_ratio):
        return None

    out_dir = output_root / split / sample.label
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = default_filename(sample.longitude, sample.latitude, sample.acq_date, sample.acq_time)
    out_path = out_dir / filename
    image.save(out_path, format="JPEG", quality=90)

    sample_id = f"{split}:{sample.label}:{filename}"
    return IngestionManifestRecord(
        sample_id=sample_id,
        label=sample.label,
        split=split,
        image_path=str(out_path),
        source_sensor=source_sensor,
        acq_date=sample.acq_date,
        acq_time=sample.acq_time,
        latitude=sample.latitude,
        longitude=sample.longitude,
        confidence=confidence,
        frp=frp,
        qa_flags=[],
        ingested_at_utc=datetime.now(timezone.utc).isoformat(),
    )


def fetch_records_with_fallback(map_key: str, config: dict) -> list[FIRMSRecord]:
    firms_cfg = config["firms"]
    sources: list[str] = firms_cfg["source_priority"]
    all_records: list[FIRMSRecord] = []
    for source in sources:
        recs = fetch_and_filter(
            map_key=map_key,
            source=source,
            area=firms_cfg["area"],
            day_range=int(firms_cfg["day_range"]),
            min_confidence=int(firms_cfg["min_confidence"]),
            daytime_only=bool(firms_cfg["daytime_only"]),
        )
        all_records.extend(recs)
    return dedupe_records(all_records)


def run_ingestion(
    records: list[FIRMSRecord],
    layer: str,
    output_root: str,
    split_ratios: tuple[float, float, float],
    negative_strategies: list[str],
    min_non_black_ratio: float,
) -> list[IngestionManifestRecord]:
    positives = positive_samples(records)
    negatives = build_negative_samples(records, strategies=negative_strategies)

    n = min(len(positives), len(negatives))
    paired: list[SamplePoint] = []
    for p, n_item in zip(positives[:n], negatives[:n]):
        paired.extend([p, n_item])

    splits = train_valid_test_split(paired, ratios=split_ratios)
    manifests: list[IngestionManifestRecord] = []

    for split, items in splits.items():
        for item in items:
            patch_req = PatchRequest(
                latitude=item.latitude,
                longitude=item.longitude,
                date=item.acq_date,
                layer=layer,
            )
            bbox = build_square_bbox(item.latitude, item.longitude, half_size_m=patch_req.half_size_m)
            url = build_getmap_url(patch_req, bbox)
            try:
                raw = fetch_patch_bytes(url)
            except Exception:
                continue

            m = save_sample(
                sample=item,
                split=split,
                output_root=Path(output_root),
                image_bytes=raw,
                source_sensor="multi-source",
                min_non_black_ratio=min_non_black_ratio,
            )
            if m:
                manifests.append(m)

    manifest_dir = Path(output_root) / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    with (manifest_dir / "latest_manifest.jsonl").open("w", encoding="utf-8") as f:
        for record in manifests:
            f.write(json.dumps(asdict(record)) + "\n")

    return manifests


def run_from_config(config_path: str, map_key: str) -> list[IngestionManifestRecord]:
    cfg = load_config(config_path)
    records = fetch_records_with_fallback(map_key, cfg)

    split_cfg = cfg["sampling"]["split_ratios"]
    split_ratios = (
        float(split_cfg["train"]),
        float(split_cfg["valid"]),
        float(split_cfg["test"]),
    )

    return run_ingestion(
        records=records,
        layer=cfg["gibs"]["layer"],
        output_root=cfg["output"]["data_root"],
        split_ratios=split_ratios,
        negative_strategies=list(cfg["sampling"].get("negative_strategy", ["spatial_buffer"])),
        min_non_black_ratio=float(cfg["quality"].get("min_non_black_ratio", 0.02)),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run FIRMS+GIBS wildfire ingestion pipeline")
    parser.add_argument("--config", default="config/pipeline.yaml", help="Path to pipeline YAML config")
    parser.add_argument("--map-key", required=True, help="NASA FIRMS MAP_KEY")
    args = parser.parse_args()

    manifests = run_from_config(config_path=args.config, map_key=args.map_key)
    print(f"ingestion complete: {len(manifests)} samples written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
