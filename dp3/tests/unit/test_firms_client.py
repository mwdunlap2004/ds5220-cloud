from src.firms_client import normalize_confidence, parse_records


CSV_TEXT = """latitude,longitude,acq_date,acq_time,confidence,frp,daynight
45.0,-75.0,2026-04-29,1530,80,12.3,D
45.1,-75.1,2026-04-29,1535,n,8.0,D
45.2,-75.2,2026-04-29,1540,90,10.0,N
"""


def test_normalize_confidence():
    assert normalize_confidence("h") == 90
    assert normalize_confidence("n") == 60
    assert normalize_confidence("75") == 75


def test_parse_records_filters_conf_and_daynight():
    records = parse_records(CSV_TEXT, source="VIIRS_SNPP_NRT", min_confidence=70, daytime_only=True)
    assert len(records) == 1
    assert records[0].confidence == 80
    assert records[0].daynight == "D"
