#!/usr/bin/env python3
"""news-image-20261126 v6 entrypoint (stdlib only).

Copies the pre-rendered entry.png into $MAKEFUN_OUTPUT_DIR and verifies it:
- exactly 1024x1024 px (read from the PNG IHDR chunk, no image library)
- at most 1 MiB
- sha256 matches the pinned value

No rendering happens here: the image was drawn locally and ships in the repo.
"""
import hashlib
import os
import shutil
import sys

EXPECTED_SHA256 = "c8ad1a75e0d987ebe6cce6da47cd21ea9bc9a2f9cbf7f4e42675e588243cd0ee"
MAX_BYTES = 1024 * 1024
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("entry.png is not a PNG file")
    if head[12:16] != b"IHDR":
        raise ValueError("entry.png has no IHDR chunk")
    w = int.from_bytes(head[16:20], "big")
    h = int.from_bytes(head[20:24], "big")
    return w, h


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        print("MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 2
    if not os.path.isfile(SRC):
        print("entry.png is missing from the repo", file=sys.stderr)
        return 2
    size = os.path.getsize(SRC)
    if size > MAX_BYTES:
        print(f"entry.png is {size} bytes, over the 1 MiB gate", file=sys.stderr)
        return 2
    w, h = png_size(SRC)
    if (w, h) != (1024, 1024):
        print(f"entry.png is {w}x{h}, expected 1024x1024", file=sys.stderr)
        return 2
    digest = sha256_file(SRC)
    if digest != EXPECTED_SHA256:
        print(f"entry.png sha256 mismatch: got {digest}, want {EXPECTED_SHA256}",
              file=sys.stderr)
        return 2
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(SRC, dst)
    if sha256_file(dst) != digest or os.path.getsize(dst) != size:
        print("copied entry.png failed verification", file=sys.stderr)
        return 2
    print(f"wrote {dst} ({size} bytes, 1024x1024, sha256 {digest[:16]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
