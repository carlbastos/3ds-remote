"""Generates meta/icon.png (48x48), meta/banner.png (256x128) and meta/audio.wav (silence)."""
import math, struct, wave, zlib, os

def png(path, w, h, px):
    raw = b"".join(b"\0" + bytes(c for x in range(w) for c in px(x, y)) for y in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

def art(w, h, scale, rounded):
    cx, cy = w / 2, h * 0.70
    def px(x, y):
        # rounded-square mask (icon only)
        if rounded:
            r, dx, dy = 8, max(0, abs(x + .5 - w / 2) - (w / 2 - 8)), max(0, abs(y + .5 - h / 2) - (h / 2 - 8))
            if dx * dx + dy * dy > r * r:
                return (0, 0, 0, 0)
        t = y / h
        bg = (int(20 + 25 * t), int(90 + 40 * t), int(200 - 30 * t))
        d = math.hypot(x + .5 - cx, y + .5 - cy) / scale
        ang = math.degrees(math.atan2(cx - (x + .5), cy - (y + .5)))
        white = (255, 255, 255, 255)
        if d < 3.2:
            return white
        if abs(ang) < 45 and any(abs(d - r) < 2.2 for r in (9, 16, 23)):
            return white
        return bg + (255,)
    return px

os.makedirs("meta", exist_ok=True)
png("meta/icon.png", 48, 48, art(48, 48, 1.15, True))
png("meta/banner.png", 256, 128, art(256, 128, 2.6, False))
with wave.open("meta/audio.wav", "wb") as wv:
    wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(22050)
    wv.writeframes(b"\0\0" * 11025)
