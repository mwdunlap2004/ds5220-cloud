from __future__ import annotations

import io

from PIL import Image, ImageStat


def decode_rgb(image_bytes: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(image_bytes))
    return img.convert("RGB")


def resize_224(image: Image.Image) -> Image.Image:
    return image.resize((224, 224), Image.Resampling.LANCZOS)


def non_black_ratio(image: Image.Image, threshold: int = 8) -> float:
    rgb = image.convert("RGB")
    pixels = list(rgb.getdata())
    non_black = sum(1 for r, g, b in pixels if max(r, g, b) > threshold)
    return non_black / max(1, len(pixels))


def is_visually_valid(image: Image.Image, min_non_black_ratio: float = 0.02) -> bool:
    ratio = non_black_ratio(image)
    if ratio < min_non_black_ratio:
        return False

    stat = ImageStat.Stat(image.convert("RGB"))
    if max(stat.mean) < 5:
        return False
    return True


def standardize_image(image_bytes: bytes) -> Image.Image:
    rgb = decode_rgb(image_bytes)
    return resize_224(rgb)
