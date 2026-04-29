from src.geo import BBox
from src.gibs_client import build_getmap_url
from src.types import PatchRequest


def test_build_getmap_url_contains_required_params():
    req = PatchRequest(latitude=45.0, longitude=-75.0, date="2026-04-29", layer="VIIRS_SNPP_CorrectedReflectance_TrueColor")
    bbox = BBox(west=-75.1, south=44.9, east=-74.9, north=45.1)
    url = build_getmap_url(req, bbox)
    assert "SERVICE=WMS" in url
    assert "REQUEST=GetMap" in url
    assert "LAYERS=VIIRS_SNPP_CorrectedReflectance_TrueColor" in url
    assert "WIDTH=224" in url
    assert "HEIGHT=224" in url
