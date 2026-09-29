import io

import numpy as np
import pytest
from PIL import Image

from grahrekha_engine.palm.image_io import MAX_LONG_EDGE, InvalidImageError, decode_image


def _encode(image: Image.Image, fmt: str = "JPEG", **kwargs: object) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format=fmt, **kwargs)
    return buf.getvalue()


def test_decodes_to_rgb_uint8_array() -> None:
    arr = decode_image(_encode(Image.new("RGB", (80, 64), (10, 20, 30))))
    assert arr.shape == (64, 80, 3)
    assert arr.dtype == np.uint8


def test_downscales_long_edge_and_keeps_aspect() -> None:
    arr = decode_image(_encode(Image.new("RGB", (4000, 3000))))
    assert max(arr.shape[:2]) == MAX_LONG_EDGE
    assert arr.shape[1] / arr.shape[0] == pytest.approx(4 / 3, rel=0.01)


def test_applies_exif_orientation() -> None:
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90° clockwise on display
    arr = decode_image(_encode(Image.new("RGB", (80, 64)), exif=exif))
    assert arr.shape[:2] == (80, 64)


def test_converts_grayscale_and_rgba_to_rgb() -> None:
    assert decode_image(_encode(Image.new("L", (64, 64)), "PNG")).shape == (64, 64, 3)
    assert decode_image(_encode(Image.new("RGBA", (64, 64)), "PNG")).shape == (64, 64, 3)


@pytest.mark.parametrize("payload", [b"", b"not an image", b"%PDF-1.4 ..."])
def test_rejects_non_images(payload: bytes) -> None:
    with pytest.raises(InvalidImageError):
        decode_image(payload)


def test_rejects_oversized_uploads() -> None:
    with pytest.raises(InvalidImageError, match="too large"):
        decode_image(b"\xff" * (20 * 1024 * 1024 + 1))


def test_rejects_decompression_bombs() -> None:
    # A tiny PNG that claims enormous dimensions must be refused before decoding.
    bomb = _encode(Image.new("1", (12000, 12000)), "PNG")
    with pytest.raises(InvalidImageError, match="dimensions"):
        decode_image(bomb)


def test_rejects_tiny_images() -> None:
    with pytest.raises(InvalidImageError, match="small"):
        decode_image(_encode(Image.new("RGB", (32, 200))))
