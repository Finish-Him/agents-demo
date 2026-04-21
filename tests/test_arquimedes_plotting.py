"""Tests for arquimedes/tools/plotting.py."""

import base64
import re
from io import BytesIO

from arquimedes.tools import plot_function


def _extract_data_uri(markdown: str) -> str:
    m = re.search(r"\((data:image/png;base64,[^\)]+)\)", markdown)
    assert m, f"no data URI in: {markdown[:200]}"
    return m.group(1)


class TestPlotting:
    def test_returns_png_data_uri(self):
        r = plot_function.invoke(
            {"expression": "x**2", "x_min": -3, "x_max": 3}
        )
        assert r.startswith("!["), r[:80]
        uri = _extract_data_uri(r)
        assert uri.startswith("data:image/png;base64,")

    def test_png_bytes_decode_to_valid_image(self):
        r = plot_function.invoke(
            {"expression": "sin(x)", "x_min": -6.28, "x_max": 6.28}
        )
        uri = _extract_data_uri(r)
        payload = uri.split(",", 1)[1]
        raw = base64.b64decode(payload)
        # PNG magic header: \x89PNG\r\n\x1a\n
        assert raw[:8] == b"\x89PNG\r\n\x1a\n"
        # Non-trivial size
        assert len(raw) > 1000

    def test_bad_expression_returns_error(self):
        r = plot_function.invoke({"expression": "%%%"})
        assert r.startswith("error")
