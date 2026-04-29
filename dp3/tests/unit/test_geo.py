from src.geo import build_square_bbox, meters_to_degree_offsets


def test_meters_to_degree_offsets_equator():
    dlat, dlon = meters_to_degree_offsets(0.0, 1250)
    assert 0.011 < dlat < 0.012
    assert 0.011 < dlon < 0.012


def test_bbox_wrap_antimeridian():
    bbox = build_square_bbox(10.0, 179.999, half_size_m=5000)
    assert -180.0 <= bbox.west <= 180.0
    assert -180.0 <= bbox.east <= 180.0
