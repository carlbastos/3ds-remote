"""Offline tests for the client: everything that does not need a 3DS on the network."""
import io
import os
import struct
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from threeds_remote import cli  # noqa: E402


def fake_cia(tid, version):
    """Smallest CIA layout cia_info() needs: header sizes plus an RSA-2048 signed TMD."""
    align = lambda n: (n + 63) & ~63
    hdr = struct.pack("<IHHIII", 0x2020, 0, 0, 0xA00, 0x350, 0xB34)
    tmd = bytearray(0xB34)
    struct.pack_into(">I", tmd, 0, 0x10004)
    struct.pack_into(">Q", tmd, 0x140 + 0x4C, tid)
    struct.pack_into(">H", tmd, 0x140 + 0x9C, version)
    data = bytearray(align(0x2020) + align(0xA00) + align(0x350))
    data[:len(hdr)] = hdr
    return bytes(data) + bytes(tmd)


class InputRedirectionTest(unittest.TestCase):
    def test_idle_packet(self):
        self.assertEqual(cli.ir_packet().hex(), "ff0f000000000002fff77f008100808000000000")

    def test_buttons_are_active_low(self):
        pad = struct.unpack_from("<I", cli.ir_packet(["A", "START"]))[0]
        self.assertEqual(pad, 0xFFF & ~0b1001)

    def test_home_is_a_special_button(self):
        self.assertEqual(struct.unpack_from("<I", cli.ir_packet(["HOME"]), 16)[0], 1)

    def test_touch_corners(self):
        touch = struct.unpack_from("<I", cli.ir_packet(touch=(319, 239)), 4)[0]
        self.assertEqual(touch, (1 << 24) | (0xFFF << 12) | 0xFFF)

    def test_unknown_button_exits(self):
        with self.assertRaises(SystemExit):
            cli.ir_packet(["Q"])


class CiaTest(unittest.TestCase):
    def test_reads_title_id_and_version(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.cia")
            with open(path, "wb") as f:
                f.write(fake_cia(0x000400000FE3D500, 48))
            self.assertEqual(cli.cia_info(path), ("000400000FE3D500", 48))

    def test_not_a_cia(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.cia")
            with open(path, "wb") as f:
                f.write(b"nope")
            self.assertIsNone(cli.cia_info(path))

    def test_version_string(self):
        self.assertEqual(cli.vstr(48), "0.3.0")
        self.assertEqual(cli.vstr((1 << 10) | (2 << 4) | 3), "1.2.3")


def tiny_jpeg(w, h):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (200, 30, 30)).save(buf, "JPEG")
    return buf.getvalue()


class ScreenshotTest(unittest.TestCase):
    def test_exif_orientation_segment(self):
        out = cli.jpeg_with_orientation(b"\xff\xd8\xff\xdbrest", 270)
        self.assertEqual(out[:4], b"\xff\xd8\xff\xe1")
        self.assertIn(b"Exif\x00\x00", out)
        self.assertEqual(struct.unpack_from(">H", out, out.index(b"\x01\x12") + 8)[0], 8)
        self.assertTrue(out.endswith(b"\xff\xdbrest"))

    def test_pillow_rotates_and_converts(self):
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("Pillow not installed")
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            out = cli.save_screen(tiny_jpeg(24, 40), os.path.join(d, "s.png"), 270)
            with Image.open(out) as img:
                self.assertEqual((img.format, img.size), ("PNG", (40, 24)))

    def test_without_pillow_falls_back_to_exif_jpeg(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(sys.modules, {"PIL": None}):
            out = cli.save_screen(b"\xff\xd8\xff\xd9", os.path.join(d, "s.png"), 270)
            self.assertTrue(out.endswith(".jpg"))
            with open(out, "rb") as f:
                self.assertEqual(f.read(4), b"\xff\xd8\xff\xe1")


class ConfigTest(unittest.TestCase):
    def test_config_path_per_os(self):
        path = cli.config_path()
        self.assertTrue(path.endswith(os.path.join("3ds-remote", "config.json")))
        if os.name == "nt":
            self.assertIn(os.environ.get("APPDATA", ""), path)

    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(cli, "CONFIG", os.path.join(d, "a", "c.json")):
            cli.save_config({"host": "10.0.0.2", "token": "secret123"})
            self.assertEqual(cli.load_config(), {"host": "10.0.0.2", "token": "secret123"})

    def test_missing_host_is_a_clear_error(self):
        with mock.patch.object(cli, "HOST", ""):
            with self.assertRaises(SystemExit) as ctx:
                cli.host_ip()
            self.assertIn("3ds login --host", str(ctx.exception))

    def test_with_port(self):
        self.assertEqual(cli.with_port("1.2.3.4"), "1.2.3.4:8080")
        self.assertEqual(cli.with_port("1.2.3.4:9000"), "1.2.3.4:9000")


if __name__ == "__main__":
    unittest.main()
