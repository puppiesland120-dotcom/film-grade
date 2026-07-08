# -*- coding: utf-8 -*-
"""
WrayWest film-emulation post-process layer (anti-slop).
Self-contained numpy + Pillow. Breaks the "clean plastic render"
signature with a real-film grade + monochrome luminance-coupled grain +
highlight roll-off + black-lift (no crush) + subtle low-key vignette.

Brand house look: low saturation, restrained contrast, warm copper/amber
midtones, faint teal lean ONLY in the shadows, near-black-but-not-crushed
blacks, highlights held below clipping. NO added glow/bloom/halation
(those ARE the slop tells on a dark brand).

Usage:
  python post.py in.png out.png [--strength 1.0] [--grain 1.0] [--seed 7]
  (strength scales the grade; grain scales grain; both default 1.0)
"""
import sys, argparse
import numpy as np
from PIL import Image


def _smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a + 1e-9), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def grade(rgb, strength=1.0):
    """rgb float [0,1] HxWx3 -> graded."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    L = 0.2126 * r + 0.7152 * g + 0.0722 * b

    shadow = _smoothstep(0.0, 0.55, 1.0 - L)          # strong in dark
    mid = 1.0 - np.abs(2.0 * L - 1.0)                  # peak at 0.5
    high = _smoothstep(0.5, 1.0, L)                    # strong in light

    out = rgb.copy()
    s = strength
    # warm copper/amber midtones (+R, -B), gentle
    out[..., 0] += mid * (0.030 * s)
    out[..., 2] -= mid * (0.026 * s)
    # faint teal lean ONLY in shadows (-R, +G, +B small)
    out[..., 0] -= shadow * (0.018 * s)
    out[..., 1] += shadow * (0.010 * s)
    out[..., 2] += shadow * (0.022 * s)
    # highlights: pull a touch warm + hold below clipping (roll-off)
    out[..., 0] += high * (0.010 * s)
    out[..., 2] -= high * (0.008 * s)

    out = np.clip(out, 0.0, 1.0)

    # black lift so shadows are near-black but NOT crushed
    blk = 0.022 * s
    out = out * (1.0 - blk) + blk

    # restrained S-curve contrast around 0.5
    c = 0.10 * s
    out = out + c * np.sin(np.clip((out - 0.5), -0.5, 0.5) * np.pi)
    out = np.clip(out, 0.0, 1.0)

    # filmic highlight roll-off (soft shoulder) to avoid harsh clipping
    knee = 0.82
    over = np.clip(out - knee, 0.0, 1.0)
    out = np.where(out > knee, knee + over / (1.0 + over / (1.0 - knee + 1e-6)) * (1.0 - knee), out)

    # global desaturation (low-sat brand)
    Lg = (0.2126 * out[..., 0] + 0.7152 * out[..., 1] + 0.0722 * out[..., 2])[..., None]
    out = out * (1.0 - 0.13 * s) + Lg * (0.13 * s)
    return np.clip(out, 0.0, 1.0)


def add_grain(rgb, amount=1.0, seed=7):
    """Monochrome film grain, coupled to luminance (peaks in mids)."""
    h, w, _ = rgb.shape
    rng = np.random.RandomState(seed)
    noise = rng.standard_normal((h, w)).astype(np.float32)
    L = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    lummask = 1.0 - np.abs(2.0 * L - 1.0)             # most grain in mids, less in deep black/white
    sigma = 0.022 * amount
    g = noise * sigma * (0.45 + 0.55 * lummask)
    return np.clip(rgb + g[..., None], 0.0, 1.0)


def vignette(rgb, amount=1.0):
    h, w, _ = rgb.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    d = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2) / np.sqrt(2.0)
    v = 1.0 - _smoothstep(0.55, 1.0, d) * (0.16 * amount)   # corners ~ -16%
    return np.clip(rgb * v[..., None], 0.0, 1.0)


def process(path_in, path_out, strength=1.0, grain=1.0, seed=7):
    im = Image.open(path_in).convert("RGB")
    arr = np.asarray(im).astype(np.float32) / 255.0
    arr = grade(arr, strength)
    arr = vignette(arr, strength)
    arr = add_grain(arr, grain, seed)
    out = (np.clip(arr, 0, 1) * 255.0 + 0.5).astype(np.uint8)
    Image.fromarray(out, "RGB").save(path_out)
    return im.size


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--grain", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    sz = process(a.inp, a.out, a.strength, a.grain, a.seed)
    print("wrote", a.out, sz)
