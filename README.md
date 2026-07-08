# film-grade

A tiny, self-contained film-emulation post-process for AI-generated images. One file, numpy + Pillow, no model downloads.

AI image generators tend to output a recognizable "clean plastic render" look: crushed blacks, clipped highlights, oversaturated color, zero grain. This script breaks that signature the way film labs did: a restrained tonal grade, monochrome luminance-coupled grain, filmic highlight roll-off, a small black lift so shadows hold detail, and a subtle low-key vignette. Deliberately NO glow, bloom, or halation, because those effects are themselves tells.

Built for the image pipeline at [wraywestblog.com](https://wraywestblog.com), where every featured image gets this pass before publish.

## Usage

```
pip install numpy pillow
python post.py in.png out.png [--strength 1.0] [--grain 1.0] [--seed 7]
```

- `--strength` scales the whole grade (0 = off, 1 = house look, >1 = heavier)
- `--grain` scales grain amount independently
- `--seed` makes grain reproducible

## What the grade does

- Warm copper/amber midtones, faint teal lean in the shadows only
- Saturation pulled down slightly, contrast restrained
- Highlights rolled off before clipping; blacks lifted, never crushed
- Monochrome grain that follows luminance (stronger in mids, calmer in deep shadow and highlight), like negative stock rather than digital noise

## Why not a LUT or a model?

A LUT cannot couple grain to luminance, and diffusion-based "make it look film" models re-render the image (and often add the glow this exists to remove). This is 150 lines of predictable math you can read.

MIT licensed. If you use it on a blog, I would love to hear about it: [wraywestblog.com/contact](https://wraywestblog.com/contact/)
