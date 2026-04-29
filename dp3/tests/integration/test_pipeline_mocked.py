import io
from pathlib import Path

from PIL import Image

from src.pipeline import run_ingestion
from src.types import FIRMSRecord


def test_pipeline_with_mocked_http(monkeypatch, tmp_path: Path):
    img = Image.new("RGB", (224, 224), color=(220, 80, 40))
    b = io.BytesIO()
    img.save(b, format="JPEG")
    payload = b.getvalue()

    def fake_fetch_patch_bytes(_url: str, timeout_s: int = 30):
        return payload

    monkeypatch.setattr("src.pipeline.fetch_patch_bytes", fake_fetch_patch_bytes)

    records = [
        FIRMSRecord(
            latitude=45.0,
            longitude=-75.0,
            acq_date="2026-04-29",
            acq_time="1530",
            confidence=90,
            frp=12.0,
            daynight="D",
            source="VIIRS_SNPP_NRT",
        )
    ]

    manifests = run_ingestion(
        records=records,
        layer="VIIRS_SNPP_CorrectedReflectance_TrueColor",
        output_root=str(tmp_path / "data"),
        split_ratios=(0.7, 0.15, 0.15),
        negative_strategies=["spatial_buffer", "temporal_displacement", "hotspot_exclusion"],
        min_non_black_ratio=0.02,
    )

    assert len(manifests) >= 1
    assert (tmp_path / "data" / "manifests" / "latest_manifest.jsonl").exists()
