"""QR code image generation with zero external dependencies.

Kodi ships no image library we can rely on across platforms, and the subtitle
dialog offers no add-on-controlled image slot (docs/kodi_ui_font_compatibility.md
section 1c) - but a custom xbmcgui.WindowDialog CAN show any local PNG through a
ControlImage. This module produces that PNG:

- QR matrix: vendored Nayuki qrcodegen (MIT, resources/lib/vendor_qrcodegen.py)
- PNG bytes: written directly with zlib from the stdlib (grayscale, no filters)
"""

import os
import struct
import zlib

from resources.lib.vendor_qrcodegen import QrCode


def _png_chunk(chunk_type, payload):
    raw = chunk_type + payload
    return struct.pack(">I", len(payload)) + raw + struct.pack(">I", zlib.crc32(raw) & 0xFFFFFFFF)


def matrix_to_png_bytes(matrix, scale=10, border=4):
    """Renders a boolean matrix (True = dark module) as a grayscale PNG.

    border is in modules (the QR quiet zone; the standard minimum is 4).
    """
    size = len(matrix)
    dim = (size + 2 * border) * scale

    rows = []
    for py in range(dim):
        my = py // scale - border
        row = bytearray([0])  # PNG filter type 0 (None) for this scanline
        for px in range(dim):
            mx = px // scale - border
            dark = 0 <= my < size and 0 <= mx < size and matrix[my][mx]
            row.append(0x00 if dark else 0xFF)
        rows.append(bytes(row))

    header = struct.pack(">IIBBBBB", dim, dim, 8, 0, 0, 0, 0)  # 8-bit grayscale
    return b"".join([
        b"\x89PNG\r\n\x1a\n",
        _png_chunk(b"IHDR", header),
        _png_chunk(b"IDAT", zlib.compress(b"".join(rows), 9)),
        _png_chunk(b"IEND", b""),
    ])


def generate_qr_png(data, path, scale=10, border=4):
    """Encodes `data` as a QR code and writes a PNG to `path`. Returns the path."""
    qr = QrCode.encode_text(data, QrCode.Ecc.MEDIUM)
    matrix = [[qr.get_module(x, y) for x in range(qr.get_size())]
              for y in range(qr.get_size())]

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(matrix_to_png_bytes(matrix, scale=scale, border=border))
    return path
