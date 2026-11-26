#!/usr/bin/env python3
"""Copy entry.png to $MAKEFUN_OUTPUT_DIR (make.fun entrypoint).

Stdlib only. This file does not render anything: entry.png is a pre-rendered
1024x1024 broadsheet (<=1 MiB) built in-session by render-ni26-v3.py.
Run: MAKEFUN_OUTPUT_DIR=<dir> python3 main.py
"""
import hashlib
import os
import shutil
import struct
import sys

MAX_BYTES = 1024 * 1024
EXPECTED = (1024, 1024)


def png_dimensions(path):
    with open(path, "rb") as fh:
        header = fh.read(33)
    if len(header) < 33 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file: %s" % path)
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        print("MAKEFUN_OUTPUT_DIR is not set; run as "
              "MAKEFUN_OUTPUT_DIR=<dir> python3 main.py", file=sys.stderr)
        return 2
    size = os.path.getsize(src)
    if size > MAX_BYTES:
        print("entry.png is %d bytes, over the 1 MiB gate" % size, file=sys.stderr)
        return 1
    dims = png_dimensions(src)
    if dims != EXPECTED:
        print("entry.png is %dx%d, expected 1024x1024" % dims, file=sys.stderr)
        return 1
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)
    if os.path.getsize(dst) != size:
        print("copied size differs from source", file=sys.stderr)
        return 1
    src_hash = sha256_file(src)
    dst_hash = sha256_file(dst)
    if src_hash != dst_hash:
        print("sha256 mismatch after copy", file=sys.stderr)
        return 1
    print("entry.png: %dx%d, %d bytes, sha256 %s" % (dims[0], dims[1], size, src_hash))
    print("copied to %s" % dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
