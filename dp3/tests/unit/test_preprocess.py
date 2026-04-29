import io

from PIL import Image

from src.preprocess import standardize_image


def test_standardize_image_rgb_224():
    img = Image.new("RGB", (512, 512), color=(200, 20, 20))
    b = io.BytesIO()
    img.save(b, format="JPEG")
    out = standardize_image(b.getvalue())
    assert out.mode == "RGB"
    assert out.size == (224, 224)
