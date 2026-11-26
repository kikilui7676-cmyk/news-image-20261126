#!/usr/bin/env python3
"""news-image-20261126 v2 entrypoint.

Copies the pre-rendered front page (entry.png, built locally with Pillow) into
the output directory the harness provides. Standard library only; no network,
no rendering, no fonts at run time. Every gate below must pass or the program
exits non-zero so a broken image can never be graded.
"""

import hashlib
import os
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "entry.png"

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1_048_576
EXPECT_WIDTH = 1024
EXPECT_HEIGHT = 1024


def fail(message):
    print(f"main.py: FAIL: {message}", file=sys.stderr)
    return 1


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        return fail("MAKEFUN_OUTPUT_DIR is not set")
    if not SOURCE.is_file():
        return fail(f"missing bundled image: {SOURCE}")

    data = SOURCE.read_bytes()
    if len(data) > MAX_BYTES:
        return fail(f"image is {len(data)} bytes, over the 1 MiB limit")
    if data[:8] != PNG_SIGNATURE:
        return fail("image does not start with the PNG signature")
    if len(data) < 33 or data[12:16] != b"IHDR":
        return fail("image has no IHDR chunk where the header belongs")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (EXPECT_WIDTH, EXPECT_HEIGHT):
        return fail(f"image is {width}x{height}, expected 1024x1024")
    bit_depth, color_type = data[24], data[25]
    if bit_depth != 8 or color_type not in (2, 6):
        return fail(f"unexpected IHDR bit depth {bit_depth} / color type {color_type}")

    digest = hashlib.sha256(data).hexdigest()
    target = Path(out_dir) / "entry.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    written = target.read_bytes()
    if written != data:
        return fail("read-back mismatch: output bytes differ from the bundled image")
    if hashlib.sha256(written).hexdigest() != digest:
        return fail("read-back mismatch: output sha256 differs from the bundled image")
    print(f"main.py: wrote {target} ({len(data)} bytes, sha256 {digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
