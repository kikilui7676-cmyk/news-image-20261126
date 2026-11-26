#!/usr/bin/env python3
"""News Image 20261126 v5 — entry program.

Copies the rendered entry.png (built in-session: 48 stories from Thursday
26 November 2026, 4 drawn leads, world map, UTC timeline, DATE CHECK audit)
into $MAKEFUN_OUTPUT_DIR/entry.png, then verifies the copy byte-for-byte
(sha256) and enforces the kit gates: at most 1024x1024 pixels and at most
1 MiB. Standard library only; no network; no writes outside the output
directory. Exits 0 on success, non-zero with a message on any failure.
"""

import hashlib
import os
import shutil
import struct
import sys
import zlib

MAX_DIM = 1024
MAX_BYTES = 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_dimensions(path):
    """Return (width, height) from the IHDR chunk; raise ValueError if the
    file is not a well-formed PNG header."""
    with open(path, "rb") as handle:
        head = handle.read(33)
    if len(head) < 33 or head[:8] != PNG_SIGNATURE:
        raise ValueError("not a PNG file (bad signature)")
    length, ctype = struct.unpack(">I4s", head[8:16])
    if ctype != b"IHDR" or length != 13:
        raise ValueError("not a PNG file (missing IHDR)")
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def png_decodable(path):
    """Confirm the PNG's image data decompresses (stdlib zlib over the
    concatenated IDAT chunks). Returns True only if it does."""
    idat = bytearray()
    with open(path, "rb") as handle:
        if handle.read(8) != PNG_SIGNATURE:
            return False
        while True:
            header = handle.read(8)
            if len(header) < 8:
                break
            length, ctype = struct.unpack(">I4s", header)
            data = handle.read(length)
            handle.read(4)  # CRC
            if ctype == b"IDAT":
                idat.extend(data)
            elif ctype == b"IEND":
                break
    try:
        zlib.decompress(bytes(idat))
    except zlib.error:
        return False
    return True


def fail(message):
    print("error: " + message, file=sys.stderr)
    return 1


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        return fail("MAKEFUN_OUTPUT_DIR is not set "
                    "(usage: MAKEFUN_OUTPUT_DIR=<dir> python3 main.py)")
    if not os.path.isfile(src):
        return fail("entry.png not found next to main.py: " + src)

    size = os.path.getsize(src)
    if size > MAX_BYTES:
        return fail("entry.png is %d bytes, over the 1 MiB gate" % size)
    try:
        width, height = png_dimensions(src)
    except ValueError as exc:
        return fail("entry.png failed PNG check: %s" % exc)
    if width > MAX_DIM or height > MAX_DIM:
        return fail("entry.png is %dx%d, over the 1024x1024 gate" % (width, height))
    if not png_decodable(src):
        return fail("entry.png image data does not decompress")

    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    src_hash = sha256_file(src)
    shutil.copyfile(src, dst)
    if sha256_file(dst) != src_hash:
        return fail("copy mismatch: sha256 differs after copying")

    print("entry.png -> " + dst)
    print("dimensions: %dx%d" % (width, height))
    print("bytes: %d" % size)
    print("sha256: " + src_hash)
    print("gates: 1024x1024 OK, 1 MiB OK, sha256 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
