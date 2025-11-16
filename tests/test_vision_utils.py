from __future__ import annotations

import base64
from io import BytesIO

from PIL import Image

from notebookmaker.vision import encode_image_base64, resize_image_if_needed


def test_resize_image_if_needed_downsizes_large_image() -> None:
    image = Image.new("RGB", (3000, 1000), color="blue")
    resized = resize_image_if_needed(image, max_width=1000, max_height=1000)
    assert resized.size[0] == 1000
    assert resized.size[1] < 1000


def test_encode_image_base64_round_trip() -> None:
    image = Image.new("RGB", (4, 4), color="red")
    encoded = encode_image_base64(image, format="PNG")
    decoded = base64.b64decode(encoded)
    loaded = Image.open(BytesIO(decoded))
    assert loaded.size == (4, 4)
