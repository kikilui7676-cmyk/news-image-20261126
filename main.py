#!/usr/bin/env python3
"""News Image 20261126 — entry runner.

Reads the pre-rendered entry.png next to this script, verifies its
integrity (SHA-256) and format gates (PNG header, max 1024x1024,
max 1 MiB), then copies it byte-identical to
$MAKEFUN_OUTPUT_DIR/entry.png (default ./output).

Standard library only. No network, no clock, no randomness.
Deterministic: the same input always produces the same output.
"""

import hashlib
import os
import shutil
import struct
import sys

EXPECTED_SHA256 = "9b5ffb01a97a21b24c43a2213149adadfcaf4f531c08508f553e1e742a143485"
SOURCE_NAME = "entry.png"
MAX_WIDTH = 1024
MAX_HEIGHT = 1024
MAX_BYTES = 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def fail(message):
    print("error: %s" % message, file=sys.stderr)
    return 1


def read_png_dimensions(data):
    """Return (width, height) from the IHDR chunk of a PNG byte string."""
    if len(data) < 33:
        raise ValueError("file too short to be a PNG")
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("not a PNG file (bad signature)")
    if data[12:16] != b"IHDR":
        raise ValueError("not a PNG file (first chunk is not IHDR)")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, SOURCE_NAME)

    try:
        with open(source, "rb") as handle:
            data = handle.read()
    except OSError as exc:
        return fail("cannot read %s: %s" % (source, exc))

    if len(data) > MAX_BYTES:
        return fail("entry.png is %d bytes, over the 1 MiB limit" % len(data))

    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        return fail(
            "sha256 mismatch: got %s, expected %s" % (digest, EXPECTED_SHA256)
        )

    try:
        width, height = read_png_dimensions(data)
    except ValueError as exc:
        return fail("PNG check failed: %s" % exc)

    if width > MAX_WIDTH or height > MAX_HEIGHT:
        return fail(
            "dimensions %dx%d exceed the %dx%d limit"
            % (width, height, MAX_WIDTH, MAX_HEIGHT)
        )

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(here, "output")
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        return fail("cannot create output directory %s: %s" % (out_dir, exc))

    dest = os.path.join(out_dir, SOURCE_NAME)
    try:
        with open(dest, "wb") as handle:
            handle.write(data)
    except OSError as exc:
        return fail("cannot write %s: %s" % (dest, exc))

    # Post-copy gate: re-read the written file and confirm it is
    # byte-identical to the verified source before reporting success.
    try:
        with open(dest, "rb") as handle:
            written = handle.read()
    except OSError as exc:
        return fail("cannot re-read %s for verification: %s" % (dest, exc))
    if written != data:
        return fail("output %s differs from verified source" % dest)
    if hashlib.sha256(written).hexdigest() != EXPECTED_SHA256:
        return fail("output sha256 mismatch after copy")

    print(
        "ok: entry.png %dx%d, %d bytes, sha256 %s -> %s"
        % (width, height, len(data), digest, dest)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
