from __future__ import annotations

import math
from dataclasses import dataclass


METERS_PER_DEGREE_LAT = 111_320.0


@dataclass(frozen=True)
class BBox:
    west: float
    south: float
    east: float
    north: float


def meters_to_degree_offsets(latitude: float, half_size_m: float) -> tuple[float, float]:
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("latitude must be within [-90, 90]")
    if half_size_m <= 0:
        raise ValueError("half_size_m must be > 0")

    delta_lat = half_size_m / METERS_PER_DEGREE_LAT
    cos_lat = math.cos(math.radians(latitude))
    cos_lat = max(abs(cos_lat), 1e-6)
    delta_lon = half_size_m / (METERS_PER_DEGREE_LAT * cos_lat)
    return delta_lat, delta_lon


def _wrap_longitude(lon: float) -> float:
    wrapped = ((lon + 180.0) % 360.0) - 180.0
    if wrapped == -180.0 and lon > 0:
        return 180.0
    return wrapped


def build_square_bbox(latitude: float, longitude: float, half_size_m: float = 1250) -> BBox:
    delta_lat, delta_lon = meters_to_degree_offsets(latitude, half_size_m)

    south = max(latitude - delta_lat, -90.0)
    north = min(latitude + delta_lat, 90.0)
    west = _wrap_longitude(longitude - delta_lon)
    east = _wrap_longitude(longitude + delta_lon)

    return BBox(west=west, south=south, east=east, north=north)


def bbox_to_wms_param(bbox: BBox) -> str:
    return f"{bbox.west:.6f},{bbox.south:.6f},{bbox.east:.6f},{bbox.north:.6f}"
