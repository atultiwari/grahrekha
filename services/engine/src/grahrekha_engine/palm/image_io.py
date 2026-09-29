"""Decode untrusted image uploads safely into RGB arrays (security boundary)."""

import io
import warnings

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 50_000_000  # refuse decompression bombs before decoding pixels
MAX_LONG_EDGE = 1600  # enough for palm creases, bounded compute and memory
MIN_SHORT_EDGE = 64

RGBImage = NDArray[np.uint8]  # shape (h, w, 3)


class InvalidImageError(ValueError):
    """The upload is not a usable image. Message is safe to show to users."""


def decode_image(data: bytes) -> RGBImage:
    if len(data) > MAX_UPLOAD_BYTES:
        raise InvalidImageError("image is too large (max 20 MB)")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(io.BytesIO(data))
            width, height = image.size
            if width * height > MAX_PIXELS:
                raise InvalidImageError("image dimensions are too large")
            image.load()
    except InvalidImageError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise InvalidImageError("image dimensions are too large") from error
    except (UnidentifiedImageError, OSError, Warning) as error:
        raise InvalidImageError("file is not a readable image") from error

    rgb: Image.Image = ImageOps.exif_transpose(image).convert("RGB")
    if min(rgb.size) < MIN_SHORT_EDGE:
        raise InvalidImageError("image is too small")
    scale = MAX_LONG_EDGE / max(rgb.size)
    if scale < 1:
        rgb = rgb.resize(
            (round(rgb.width * scale), round(rgb.height * scale)), Image.Resampling.LANCZOS
        )
    # EXIF and other metadata are dropped here: only pixels leave this function.
    return np.asarray(rgb, dtype=np.uint8).copy()
