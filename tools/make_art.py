#!/usr/bin/env python3
"""Renders meta/banner.png (256x128) and meta/icon.png (48x48), and writes meta/audio.wav (silence).

The scene is real 3D: a small sphere-tracer over signed distance fields draws a two-screen
handheld with an antenna beaming Wi-Fi waves at a laptop. Run it only when the art changes;
the PNGs are committed. Needs numpy and Pillow; the title font is macOS's Avenir Next.

    python3 tools/make_art.py            # writes meta/banner.png, meta/icon.png, meta/audio.wav
    python3 tools/make_art.py --preview  # also writes 4x previews to build/art-*.png
"""
import math
import os
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FONT = "/System/Library/Fonts/Avenir Next.ttc"
FONT_HEAVY = 8

# ---------------------------------------------------------------- vector helpers

def v(*a):
    return np.array(a, dtype=np.float64)


def norm(a):
    return a / np.linalg.norm(a, axis=-1, keepdims=True)


def length(a):
    return np.linalg.norm(a, axis=-1)


def rot_y(p, ang):            # rotate points about the y axis
    c, s = math.cos(ang), math.sin(ang)
    x, z = p[:, 0] * c + p[:, 2] * s, -p[:, 0] * s + p[:, 2] * c
    return np.stack([x, p[:, 1], z], 1)


def rot_x(p, ang):            # rotate points about the x axis (+z towards +y)
    c, s = math.cos(ang), math.sin(ang)
    y, z = p[:, 1] * c + p[:, 2] * s, -p[:, 1] * s + p[:, 2] * c
    return np.stack([p[:, 0], y, z], 1)


def rot_z(p, ang):
    c, s = math.cos(ang), math.sin(ang)
    x, y = p[:, 0] * c - p[:, 1] * s, p[:, 0] * s + p[:, 1] * c
    return np.stack([x, y, p[:, 2]], 1)

# ---------------------------------------------------------------- SDF primitives

def sd_round_box(p, half, r):
    q = np.abs(p) - (half - r)
    return length(np.maximum(q, 0)) + np.minimum(q.max(1), 0) - r


def sd_capsule(p, a, b, r):
    pa, ba = p - a, b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return length(pa - h[:, None] * ba) - r


def sd_sphere(p, c, r):
    return length(p - c) - r


def sd_capped_torus(p, half_angle, ra, rb):
    """Arc in the xy plane, symmetric about +y (Inigo Quilez's capped torus)."""
    sc = (math.sin(half_angle), math.cos(half_angle))
    px = np.abs(p[:, 0])
    py = p[:, 1]
    k = np.where(sc[1] * px > sc[0] * py, px * sc[0] + py * sc[1], np.hypot(px, py))
    return np.sqrt(np.maximum(px * px + py * py + p[:, 2] ** 2 + ra * ra - 2 * ra * k, 0)) - rb

# ---------------------------------------------------------------- scene

class Clamshell:
    """A base slab and a lid hinged on its back edge, turned by `yaw` around its centre."""

    def __init__(self, centre, half, lid_thick, open_deg, yaw_deg, r):
        self.c = v(*centre)
        self.half = v(*half)                 # base half extents
        self.lt = lid_thick                  # lid half thickness
        self.open = math.radians(open_deg)
        self.yaw = math.radians(yaw_deg)
        self.r = r

    def local(self, p):
        return rot_y(p - self.c, -self.yaw)

    def lid_local(self, p):
        q = self.local(p) - v(0, 2 * self.half[1], -self.half[2])   # hinge at the origin
        return rot_x(q, -self.open)

    def base_sdf(self, p):
        return sd_round_box(self.local(p) - v(0, self.half[1], 0), self.half, self.r)

    def lid_sdf(self, p):
        hz = self.half[2]
        return sd_round_box(self.lid_local(p) - v(0, self.lt, hz), v(self.half[0], self.lt, hz), self.r)

    def to_world(self, q_lid):
        """A point in lid-local coordinates to world space."""
        q = rot_x(q_lid[None], self.open)[0] + v(0, 2 * self.half[1], -self.half[2])
        return rot_y(q[None], self.yaw)[0] + self.c


DS = Clamshell(centre=(-1.45, 0, 0.15), half=(0.62, 0.055, 0.40), lid_thick=0.04,
               open_deg=104, yaw_deg=22, r=0.035)
LAPTOP = Clamshell(centre=(1.35, 0, -0.15), half=(1.05, 0.035, 0.68), lid_thick=0.022,
                   open_deg=106, yaw_deg=-24, r=0.02)

# Antenna on the handheld lid's far right corner, pointing up and slightly outwards.
ANT_BASE = DS.to_world(v(DS.half[0] - 0.09, DS.lt, 2 * DS.half[2] - 0.05))
ANT_TIP = ANT_BASE + v(0.05, 0.55, 0)

# Waves fan out from the antenna tip towards the laptop screen.
_screen_mid = LAPTOP.to_world(v(0, 0, LAPTOP.half[2]))
_d = _screen_mid - ANT_TIP
WAVE_DIR = math.atan2(_d[1], _d[0])
WAVE_RADII = (0.30, 0.55, 0.80)

M_DS, M_LAPTOP, M_ANT, M_TIP, M_WAVE = range(5)
SHOW_LAPTOP = True          # the icon leaves the laptop out


def wave_local(p):
    q = rot_z(p - ANT_TIP, -WAVE_DIR)        # beam direction -> +x
    return np.stack([q[:, 1], q[:, 0], q[:, 2]], 1)   # capped torus is symmetric about +y


def scene(p, with_ids=False):
    d = [
        np.minimum(DS.base_sdf(p), DS.lid_sdf(p)),
        np.minimum(LAPTOP.base_sdf(p), LAPTOP.lid_sdf(p)) if SHOW_LAPTOP else np.full(len(p), 1e9),
        sd_capsule(p, ANT_BASE, ANT_TIP, 0.022),
        sd_sphere(p, ANT_TIP, 0.06),
    ]
    q = wave_local(p)
    d.append(np.min([sd_capped_torus(q, math.radians(38), r, 0.032) for r in WAVE_RADII], 0))
    d = np.stack(d, 1)
    return (d.min(1), d.argmin(1)) if with_ids else d.min(1)


def normal(p):
    e = 1e-3
    n = np.stack([scene(p + v(*o) * e) - scene(p - v(*o) * e) for o in np.eye(3)], 1)
    return norm(n)


def march(ro, rd, tmax=30.0, steps=160):
    t = np.zeros(len(rd))
    hit = np.zeros(len(rd), bool)
    alive = np.ones(len(rd), bool)
    for _ in range(steps):
        idx = np.nonzero(alive)[0]
        if not len(idx):
            break
        d = scene(ro[idx] + rd[idx] * t[idx, None])
        t[idx] += d
        done = d < 4e-4 * np.maximum(t[idx], 1)
        hit[idx[done]] = True
        alive[idx[done | (t[idx] > tmax)]] = False
    return t, hit


def soft_shadow(p, l, k=10.0, steps=48):
    res = np.ones(len(p))
    t = np.full(len(p), 0.02)
    for _ in range(steps):
        h = scene(p + l * t[:, None])
        res = np.minimum(res, np.clip(k * h / t, 0, 1))
        t += np.clip(h, 0.01, 0.25)
    return np.clip(res, 0, 1)


def ambient_occlusion(p, n):
    occ = np.zeros(len(p))
    for i in range(1, 6):
        h = 0.03 * i
        occ += (h - scene(p + n * h)) / (2 ** i)
    return np.clip(1 - 4 * occ, 0, 1)

# ---------------------------------------------------------------- materials

def surface_colour(p, n, mid):
    """Albedo, emission, shininess and specular strength per hit point."""
    N = len(p)
    albedo = np.zeros((N, 3))
    emit = np.zeros((N, 3))
    shine = np.full(N, 40.0)
    spec = np.full(N, 0.35)

    # handheld: glossy coral body; screens are glowing panels
    m = mid == M_DS
    albedo[m] = v(0.80, 0.12, 0.10)
    shine[m], spec[m] = 90, 0.6
    if m.any():
        idx = np.nonzero(m)[0]
        pl = DS.lid_local(p[idx])
        on_lid_face = (pl[:, 1] < 0.012) & (np.abs(pl[:, 0]) < DS.half[0] * 0.72) & \
                      (pl[:, 2] > 0.12) & (pl[:, 2] < 2 * DS.half[2] - 0.12)
        pb = DS.local(p[idx])
        on_base_top = pb[:, 1] > 2 * DS.half[1] - 0.006
        bottom_scr = on_base_top & (np.abs(pb[:, 0]) < DS.half[0] * 0.48) & \
                     (pb[:, 2] > -DS.half[2] + 0.06) & (pb[:, 2] < DS.half[2] - 0.16)
        pad = on_base_top & (np.hypot(pb[:, 0] + DS.half[0] * 0.77, pb[:, 2] + 0.08) < 0.075)
        btn = np.zeros(len(idx), bool)
        for bx, bz in ((0.06, 0), (-0.06, 0), (0, 0.06), (0, -0.06)):
            btn |= on_base_top & (np.hypot(pb[:, 0] - DS.half[0] * 0.77 - bx, pb[:, 2] + 0.08 - bz) < 0.025)
        u = np.clip((pl[:, 2] - 0.12) / (2 * DS.half[2] - 0.24), 0, 1)
        top_glow = np.stack([0.25 + 0.3 * u, 0.65 + 0.25 * u, 1.0 + 0 * u], 1)
        albedo[idx[on_lid_face]] = 0.02
        emit[idx[on_lid_face]] = top_glow[on_lid_face] * 1.1
        albedo[idx[bottom_scr]] = 0.02
        emit[idx[bottom_scr]] = v(0.35, 0.80, 0.95) * 0.9
        albedo[idx[pad | btn]] = v(0.12, 0.12, 0.14)

    # laptop: brushed aluminium, dark keyboard, terminal-like screen
    m = mid == M_LAPTOP
    albedo[m] = v(0.72, 0.74, 0.78)
    shine[m], spec[m] = 60, 0.5
    if m.any():
        idx = np.nonzero(m)[0]
        pl = LAPTOP.lid_local(p[idx])
        H, D = LAPTOP.half[0], 2 * LAPTOP.half[2]
        scr = (pl[:, 1] < 0.008) & (np.abs(pl[:, 0]) < H - 0.07) & (pl[:, 2] > 0.07) & (pl[:, 2] < D - 0.07)
        sx = (pl[:, 0] + H - 0.07) / (2 * H - 0.14)           # 0..1 left to right
        sy = (D - 0.07 - pl[:, 2]) / (D - 0.14)                # 0..1 top to bottom
        line = np.floor(sy * 9)
        in_line = (np.mod(sy * 9, 1) > 0.3) & (np.mod(sy * 9, 1) < 0.7)
        rng = np.mod(np.sin(line * 12.9898) * 43758.5453, 1)
        text = in_line & (sx > 0.08) & (sx < 0.08 + 0.25 + 0.6 * rng) & (line >= 1) & (line <= 7)
        base_glow = np.stack([0.03 + 0.05 * sy, 0.10 + 0.12 * sy, 0.25 + 0.15 * sy], 1)
        glow = np.where(text[:, None], v(0.45, 0.95, 0.75), base_glow)
        albedo[idx[scr]] = 0.02
        emit[idx[scr]] = glow[scr] * 1.2
        pb = LAPTOP.local(p[idx])
        top = pb[:, 1] > 2 * LAPTOP.half[1] - 0.005
        kx, kz = pb[:, 0], pb[:, 2]
        kb = top & (np.abs(kx) < H - 0.12) & (kz > -LAPTOP.half[2] + 0.08) & (kz < 0.1)
        key_gap = (np.mod(kx / 0.13, 1) < 0.12) | (np.mod(kz / 0.13, 1) < 0.12)
        pad = top & (np.abs(kx) < 0.30) & (kz > 0.22) & (kz < LAPTOP.half[2] - 0.08)
        albedo[idx[kb & ~key_gap]] = v(0.10, 0.10, 0.12)
        albedo[idx[kb & key_gap]] = v(0.30, 0.31, 0.34)
        albedo[idx[pad]] = v(0.62, 0.64, 0.68)

    m = mid == M_ANT
    albedo[m] = v(0.25, 0.25, 0.28)
    shine[m], spec[m] = 120, 0.9
    m = mid == M_TIP
    albedo[m] = v(1.0, 0.25, 0.2)
    emit[m] = v(1.0, 0.35, 0.25) * 0.9
    m = mid == M_WAVE
    albedo[m] = v(0.4, 0.9, 1.0)
    emit[m] = v(0.30, 0.85, 1.0) * 1.3
    shine[m], spec[m] = 80, 0.4
    return albedo, emit, shine, spec

# ---------------------------------------------------------------- rendering

def render(w, h, eye, target, fov_deg, bg_top, bg_bottom):
    eye, target = v(*eye), v(*target)
    fwd = norm(target - eye)
    right = norm(np.cross(fwd, v(0, 1, 0)))
    up = np.cross(right, fwd)
    f = 1 / math.tan(math.radians(fov_deg) / 2)
    xs = (np.arange(w) + 0.5) / w * 2 - 1
    ys = 1 - (np.arange(h) + 0.5) / h * 2
    X, Y = np.meshgrid(xs * w / h, ys)
    rd = norm(X.reshape(-1, 1) * right + Y.reshape(-1, 1) * up + f * fwd)
    ro = np.broadcast_to(eye, rd.shape)

    # background: vertical gradient, darker towards the floor
    t_bg = (Y.reshape(-1) + 1) / 2
    col = np.outer(1 - t_bg, bg_bottom) + np.outer(t_bg, bg_top)
    alpha = np.ones(len(rd))

    t, hit = march(ro, rd)
    L = norm(v(-0.55, 0.85, 0.65))
    L2 = norm(v(0.8, 0.3, 0.4))

    # floor y=0: only shadows and a faint reflection-free sheen
    tf = np.where(rd[:, 1] < 0, -eye[1] / np.minimum(rd[:, 1], -1e-6), np.inf)
    floor = ~hit & np.isfinite(tf) & (tf < 40)
    floor |= hit & (tf < t)
    if floor.any():
        idx = np.nonzero(floor)[0]
        pf = eye + rd[idx] * tf[idx, None]
        sh = soft_shadow(pf + v(0, 1e-3, 0), L, k=6)
        ao = ambient_occlusion(pf, np.tile(v(0, 1, 0), (len(idx), 1)))
        dark = 1 - 0.55 * (1 - sh * ao)
        col[idx] *= dark[:, None]
        hit[idx] = False

    idx = np.nonzero(hit)[0]
    if len(idx):
        p = eye + rd[idx] * t[idx, None]
        _, mid = scene(p, with_ids=True)
        n = normal(p)
        albedo, emit, shine, spec = surface_colour(p, n, mid)
        sh = soft_shadow(p + n * 2e-3, L)
        ao = ambient_occlusion(p, n)
        ndl = np.clip(n @ L, 0, 1) * sh
        ndl2 = np.clip(n @ L2, 0, 1) * 0.35
        hv = norm(L - rd[idx])
        sp = spec * np.clip(np.sum(n * hv, 1), 0, 1) ** shine * sh
        fres = (1 - np.clip(-np.sum(n * rd[idx], 1), 0, 1)) ** 4
        sky = 0.25 + 0.15 * n[:, 1]
        lit = albedo * (1.15 * ndl[:, None] * v(1.0, 0.96, 0.9) + ndl2[:, None] * v(0.5, 0.7, 1.0)
                        + (sky * ao)[:, None] * v(0.55, 0.65, 0.9))
        lit += sp[:, None] + (0.25 * fres * ao)[:, None] * v(0.5, 0.7, 1.0) + emit
        col[idx] = lit

    img = np.clip(col.reshape(h, w, 3), 0, None)
    # glow: blur what is emissive and add it back
    em = np.zeros((h * w, 3))
    if len(idx):
        em[idx] = emit
    em = em.reshape(h, w, 3)
    em_img = Image.fromarray((np.clip(em, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8))
    blur = np.asarray(em_img.filter(ImageFilter.GaussianBlur(w / 70)), np.float64) / 255
    img = img + 0.55 * blur ** 2.2
    img = img / (1 + img * 0.25)                      # gentle tone map
    img = np.clip(img, 0, 1) ** (1 / 2.2)
    return Image.fromarray((img * 255).astype(np.uint8), "RGB")


def draw_title(img, text, sub, scale):
    """Heavy white title with a stepped blue extrusion, plus a small subtitle."""
    d = ImageDraw.Draw(img)
    W, H = img.size
    font = ImageFont.truetype(FONT, 25 * scale, index=FONT_HEAVY)
    small = ImageFont.truetype(FONT, 10 * scale, index=5)
    tw = d.textlength(text, font=font)
    x, y = (W - tw) / 2, H - 45 * scale
    for i in range(3 * scale, 0, -1):                  # extrusion, darker the deeper
        k = i / (3 * scale)
        d.text((x + i * 0.6, y + i), text, font=font, fill=(int(20 + 20 * (1 - k)), int(50 + 40 * (1 - k)), int(110 + 60 * (1 - k))))
    mask = Image.new("L", img.size)
    ImageDraw.Draw(mask).text((x, y), text, font=font, fill=255)
    grad = Image.linear_gradient("L").resize(img.size)
    top = Image.new("RGB", img.size, (255, 255, 255))
    bot = Image.new("RGB", img.size, (180, 225, 255))
    face = Image.composite(bot, top, grad.point(lambda g: min(255, max(0, (g - (y / H * 255)) * 6))))
    img.paste(face, (0, 0), mask)
    sw = d.textlength(sub, font=small)
    d.text(((W - sw) / 2, H - 16 * scale), sub, font=small, fill=(170, 200, 235))


def main():
    preview = "--preview" in sys.argv
    meta = os.path.join(ROOT, "meta")
    s = 4                                                # supersampling

    banner = render(256 * s, 128 * s, eye=(0.15, 2.1, 6.4), target=(0.0, 0.35, 0), fov_deg=34,
                    bg_top=v(0.10, 0.20, 0.42), bg_bottom=v(0.02, 0.05, 0.13))
    shade = Image.linear_gradient("L").resize(banner.size).point(lambda g: int(max(0, g - 150) * 2.2))
    banner = Image.composite(Image.new("RGB", banner.size, (4, 10, 28)), banner, shade)
    draw_title(banner, "3DS Remote", "control your 3DS over Wi-Fi", s)
    if preview:
        os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
        banner.save(os.path.join(ROOT, "build", "art-banner.png"))
    banner.resize((256, 128), Image.LANCZOS).convert("RGBA").save(os.path.join(meta, "banner.png"))

    global SHOW_LAPTOP
    SHOW_LAPTOP = False
    icon = render(48 * 8, 48 * 8, eye=(-0.5, 1.75, 3.7), target=(-1.10, 0.82, 0), fov_deg=36.5,
                  bg_top=v(0.16, 0.34, 0.66), bg_bottom=v(0.04, 0.10, 0.25))
    if preview:
        icon.save(os.path.join(ROOT, "build", "art-icon.png"))
    icon.resize((48, 48), Image.LANCZOS).convert("RGBA").save(os.path.join(meta, "icon.png"))
    with wave.open(os.path.join(meta, "audio.wav"), "wb") as wv:   # the banner needs a sound; keep it silent
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(22050)
        wv.writeframes(b"\0\0" * 11025)
    print("wrote meta/banner.png, meta/icon.png and meta/audio.wav")


if __name__ == "__main__":
    main()
