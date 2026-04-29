from src.sampler import build_negative_samples
from src.types import FIRMSRecord


def test_build_negative_samples_with_exclusion_and_temporal():
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

    negatives = build_negative_samples(records, strategies=["spatial_buffer", "temporal_displacement", "hotspot_exclusion"])
    assert len(negatives) >= 1
    assert all(n.label == "nowildfire" for n in negatives)
