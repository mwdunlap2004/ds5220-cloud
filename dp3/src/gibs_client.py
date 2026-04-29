from __future__ import annotations

from urllib.parse import urlencode

import requests

from .geo import BBox, bbox_to_wms_param
from .types import PatchRequest


GIBS_WMS_BASE = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"


def build_getmap_url(request: PatchRequest, bbox: BBox) -> str:
    params = {
        "SERVICE": "WMS",
        "REQUEST": "GetMap",
        "VERSION": "1.1.1",
        "LAYERS": request.layer,
        "STYLES": "",
        "SRS": "EPSG:4326",
        "BBOX": bbox_to_wms_param(bbox),
        "WIDTH": str(request.width),
        "HEIGHT": str(request.height),
        "FORMAT": request.image_format,
        "TIME": request.date,
    }
    return f"{GIBS_WMS_BASE}?{urlencode(params)}"


def fetch_patch_bytes(url: str, timeout_s: int = 30) -> bytes:
    resp = requests.get(url, timeout=timeout_s)
    resp.raise_for_status()
    return resp.content
