#!/usr/bin/env python3
"""Writes a full X.Y.Z title version into a CIA's TMD and ticket.

makerom 0.19.0 ignores -ver/-major/-minor/-micro when building from an ELF and only takes the
major part from the RSF's RemasterVersion, so the version is patched in afterwards. Neither
field is covered by a content hash; the signatures are already fake-signed (Luma ignores them).

Usage: set-cia-version.py file.cia X.Y.Z
"""
import struct
import sys

SIG_BODY = {0x10003: 0x240, 0x10004: 0x140, 0x10005: 0x80}  # signature type -> header offset


def align(n):
    return (n + 63) & ~63


def encode(version):
    major, minor, micro = (int(p) for p in version.split("."))
    if not (0 <= major < 64 and 0 <= minor < 64 and 0 <= micro < 16):
        sys.exit(f"version {version} out of range (major/minor 0-63, micro 0-15)")
    return (major << 10) | (minor << 4) | micro


def main():
    path, version = sys.argv[1], sys.argv[2]
    v = encode(version)
    data = bytearray(open(path, "rb").read())
    hdr_size, _type, _fmt, cert_size, tik_size, tmd_size = struct.unpack_from("<IHHIII", data, 0)
    tik = align(hdr_size) + align(cert_size)
    tmd = tik + align(tik_size)

    for name, base, field in (("ticket", tik, 0xA6), ("tmd", tmd, 0x9C)):
        sig = struct.unpack_from(">I", data, base)[0]
        if sig not in SIG_BODY:
            sys.exit(f"unexpected {name} signature type {sig:#x}")
        struct.pack_into(">H", data, base + SIG_BODY[sig] + field, v)

    open(path, "wb").write(data)
    print(f"{path}: title version {version} ({v})")


if __name__ == "__main__":
    main()
