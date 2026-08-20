"""Covers QR generation (resources/lib/qr.py) and the QR dialog fallback path."""
import struct
import zlib
from unittest.mock import MagicMock, patch

from resources.lib.qr import generate_qr_png, matrix_to_png_bytes
from resources.lib.vendor_qrcodegen import QrCode


def _parse_png(data):
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "PNG signature missing"
    width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    idat_start = data.index(b"IDAT") + 4
    idat_len = struct.unpack(">I", data[idat_start - 8:idat_start - 4])[0]
    raw = zlib.decompress(data[idat_start:idat_start + idat_len])
    return width, height, bit_depth, color_type, raw


def test_png_bytes_are_a_valid_grayscale_image():
    matrix = [[True, False], [False, True]]
    png = matrix_to_png_bytes(matrix, scale=2, border=1)

    width, height, bit_depth, color_type, raw = _parse_png(png)
    assert width == height == (2 + 2) * 2  # (size + 2*border) * scale
    assert (bit_depth, color_type) == (8, 0)  # 8-bit grayscale
    assert len(raw) == height * (width + 1)  # +1 filter byte per scanline
    assert png.endswith(_iend())


def _iend():
    return struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)


def test_dark_modules_are_black_and_quiet_zone_is_white():
    matrix = [[True]]
    png = matrix_to_png_bytes(matrix, scale=1, border=1)
    _w, _h, _bd, _ct, raw = _parse_png(png)

    # 3x3 image, rows prefixed with filter byte: quiet zone white, center black
    rows = [raw[i * 4 + 1:i * 4 + 4] for i in range(3)]
    assert rows[0] == b"\xff\xff\xff"
    assert rows[1] == b"\xff\x00\xff"
    assert rows[2] == b"\xff\xff\xff"


def test_generated_file_round_trips_the_qr_matrix(tmp_path):
    url = "https://www.opensubtitles.com/newuser"
    path = str(tmp_path / "qr.png")

    generate_qr_png(url, path, scale=3, border=4)

    qr = QrCode.encode_text(url, QrCode.Ecc.MEDIUM)
    with open(path, "rb") as f:
        width, height, _bd, _ct, raw = _parse_png(f.read())

    expected_dim = (qr.get_size() + 8) * 3
    assert width == height == expected_dim

    # Spot-check the three finder patterns: their centers must be dark.
    def pixel(mx, my):
        px, py = (mx + 4) * 3 + 1, (my + 4) * 3 + 1
        return raw[py * (width + 1) + 1 + px]

    size = qr.get_size()
    for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):
        assert pixel(cx, cy) == 0, f"finder center at ({cx},{cy}) should be dark"


def test_show_qr_falls_back_to_text_dialog_when_generation_fails():
    from resources.lib import qr_dialog

    dialog = MagicMock()
    with patch("resources.lib.qr_dialog.generate_qr_png", side_effect=OSError("disk full")), \
         patch("resources.lib.qr_dialog.xbmcgui.Dialog", return_value=dialog), \
         patch("resources.lib.qr_dialog.QRWindow") as window:
        qr_dialog.show_qr("https://www.opensubtitles.com", "Heading")

    dialog.ok.assert_called_once_with("Heading", "https://www.opensubtitles.com")
    window.assert_not_called()
