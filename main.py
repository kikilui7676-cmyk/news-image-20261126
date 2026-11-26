#!/usr/bin/env python3
"""news-image-20261126 v4: copy the pre-rendered entry image to the output dir.

The image (entry.png, 1024x1024, one page summing up 26 November 2026's world
news: 45 stories, 7 regions) is built by the author in this session and shipped
in the repository. This program does no rendering and no network: it copies the
file, then verifies the copy byte-for-byte (SHA-256) and checks the PNG header
and dimensions before reporting success.
"""

import hashlib
import os
import shutil
import struct
import sys

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
EXPECTED_SIZE = 1024 * 1024  # kit limit: image at most 1 MiB, 1024x1024 px


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_dimensions(path):
    with open(path, "rb") as handle:
        header = handle.read(33)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file (bad signature)")
    if header[12:16] != b"IHDR":
        raise ValueError("not a PNG file (missing IHDR)")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        print("MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 1
    if not os.path.isfile(SOURCE):
        print("entry.png missing next to main.py", file=sys.stderr)
        return 1
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    expected = sha256_of(SOURCE)
    width, height = png_dimensions(SOURCE)
    if (width, height) != (1024, 1024):
        print(f"entry.png is {width}x{height}, expected 1024x1024",
              file=sys.stderr)
        return 1
    shutil.copyfile(SOURCE, target)
    actual = sha256_of(target)
    if actual != expected:
        print("copy verification failed: sha256 mismatch", file=sys.stderr)
        return 1
    copied_w, copied_h = png_dimensions(target)
    if (copied_w, copied_h) != (1024, 1024):
        print(f"copied file is {copied_w}x{copied_h}, expected 1024x1024",
              file=sys.stderr)
        return 1
    size = os.path.getsize(target)
    if size > EXPECTED_SIZE:
        print(f"entry.png is {size} bytes, over the 1 MiB limit",
              file=sys.stderr)
        return 1
    print(f"wrote {target} ({width}x{height}, {size} bytes, sha256 {actual})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
