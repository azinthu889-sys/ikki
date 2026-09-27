# -*- coding: utf-8 -*-
"""Kinetic keyword titles locked to the spoken word (short-916, Zin 2026-09-27).

Reference r3 measured frame by frame (reports/zae_short_r3_layers_2026-09-27.md):
- a title word appears as it is spoken: FREEZE 3.97 s vs the word at 3.99 s,
  FRAME 4.37 vs 4.35 -> on = word start - 0.02 s
- entrance: blur + fade, 0.27 s (8 frames at 30 fps)
- the next word of the group stacks under it as it is spoken (+0.4 s there)
- hold 1.0-1.2 s after the last word, fade out 0.3 s
- white, soft dark drop shadow; 4 section groups + intro + outro in 42 s

Text is the keyword exactly as transcribed (R1: nothing added or changed), so a
title can only be a word the speaker actually says, at the moment it is said.
Placement: the chest band between the face zone and the caption top; groups
never overlap a graphic window.
"""
import os
import numpy as np

ON_LEAD = 0.02
ENTER = 0.27
HOLD = 1.1
EXIT = 0.30
MAX_GROUP = 2.8

def groups(caps, avoid, dur, gap=6.0, max_words=2, first_ok=0.3):
    """-> [dict(tokens=[(text, t_on)], a, b)] on the cut timeline."""
    out = []; last_end = -9.0
    for c in caps:
        kws = [k for k in (c.get("kw") or []) if k and k.strip()]
        ws = c.get("words") or []
        if not kws or not ws: continue
        toks = []
        for k in kws:
            hit = next((w for w in ws if k in str(w[0]) or str(w[0]) in k and len(str(w[0])) > 1), None)
            if hit is None: continue
            t = float(hit[1]) - ON_LEAD
            if all(abs(t - x[1]) > 0.05 for x in toks): toks.append((k, t))
        toks = sorted(toks, key=lambda x: x[1])[:max_words]
        if not toks: continue
        a = max(0.0, toks[0][1]); b = min(a + MAX_GROUP, toks[-1][1] + ENTER + HOLD) + EXIT
        if a < first_ok or b > dur - 0.2 or a - last_end < gap: continue
        if any(not (b + 0.3 <= x or a - 0.3 >= y) for x, y in avoid): continue
        out.append(dict(tokens=[(k, max(0.0, t)) for k, t in toks], a=round(a, 3), b=round(b, 3)))
        last_end = b
    return out

def render(gs, out, work, W, H, size, font, fallback, ct, fps=30, total=None, y_top=None,
           y_max=None, maxw=None, log=None):
    """alpha qtrle .mov (W x band) with every group's animation; returns (out, y_top) or None"""
    from PIL import Image, ImageFilter
    import subprocess
    work = os.path.abspath(work); out = os.path.abspath(out)
    os.makedirs(work, exist_ok=True)
    maxw = maxw or int(W * 0.84)
    line = int(size * 1.22)
    band = line + int(size * 0.9)          # one line + room for the glow
    y_top = int(H * 0.57) if y_top is None else int(y_top)
    if y_max is not None and y_top + band > y_max:
        band = max(line + int(size * 0.3), y_max - y_top)
    # render every token once (cttext shapes Burmese), crop to ink
    def tok_png(txt, i, size=size):
        p = os.path.join(work, f"kt{i:03d}.png")
        sz = size
        for _ in range(6):
            ct(dict(text=txt, font=font, fallback=fallback, size=sz, w=W, h=int(sz * 2.4),
                    fill="#FFFFFF", unit="cluster", align="center",
                    shadow=dict(dx=0, dy=max(2, int(sz * 0.07)), blur=max(3, int(sz * 0.18)), alpha=0.85),
                    frames=[{"out": p, "words": []}]))
            im = Image.open(p).convert("RGBA"); a = np.asarray(im)[:, :, 3]
            xs = np.nonzero(a.max(0) > 8)[0]; ys = np.nonzero(a.max(1) > 8)[0]
            if len(xs) == 0: return None, 0
            if xs[-1] - xs[0] <= maxw or sz <= int(size * 0.6): break
            sz = int(sz * 0.9)
        pad = int(sz * 0.35)
        im = im.crop((max(0, xs[0] - pad), max(0, ys[0] - pad), min(W, xs[-1] + pad), min(im.height, ys[-1] + pad)))
        # soft dark glow under the ink: the title sits on the chest, often a
        # white shirt, where r3's drop shadow alone would not separate it
        al = np.asarray(im)[:, :, 3].astype(np.float32)
        g = Image.fromarray(al.astype(np.uint8)).filter(ImageFilter.GaussianBlur(sz * 0.20))
        glow = np.zeros((im.height, im.width, 4), np.uint8)
        glow[:, :, 3] = np.clip(np.asarray(g, np.float32) * 1.4, 0, 215).astype(np.uint8)
        # r3 look: white at the top of the ink fading to light grey at the bottom
        rgb = np.asarray(im).copy().astype(np.float32)
        ys = np.nonzero(al.max(1) > 8)[0]
        if len(ys):
            ramp = np.clip((np.arange(im.height) - ys[0]) / max(1, ys[-1] - ys[0]), 0, 1)
            k = (1.0 - 0.22 * ramp)[:, None]
            lit = rgb[:, :, :3].min(2) > 200                      # the white fill, not the shadow
            for c in range(3): rgb[:, :, c] = np.where(lit, rgb[:, :, c] * k, rgb[:, :, c])
        im = Image.fromarray(rgb.astype(np.uint8), "RGBA")
        base = Image.fromarray(glow, "RGBA"); base.alpha_composite(im)
        return base, pad
    n = 0; timed = []
    blank = os.path.join(work, "_kblank.png"); Image.new("RGBA", (W, band), (0, 0, 0, 0)).save(blank)
    fr = 1.0 / fps
    for g in gs:
        sz_g = size; ims = []
        for _try in range(4):
            ims = []
            for txt, t in g["tokens"]:
                im, pad = tok_png(txt, n, sz_g); n += 1
                if im is not None: ims.append((im, t, pad))
            ink = sum(im.width - 2 * pd for im, _, pd in ims) + int(sz_g * 0.28) * (len(ims) - 1)
            if not ims or ink <= maxw or sz_g <= int(size * 0.7): break
            sz_g = int(sz_g * 0.88)
        if not ims: continue
        if ink > maxw: ims = ims[:1]                      # one line only: keep the first word
        # one line, words side by side, centred on ink (the glow pad may overlap)
        gapx = int(sz_g * 0.28)
        ink = sum(im.width - 2 * pd for im, _, pd in ims) + gapx * (len(ims) - 1)
        pos = []; x = (W - ink) // 2
        for im, _, pd in ims:
            pos.append((x - pd, (band - im.height) // 2)); x += im.width - 2 * pd + gapx
        ims = [(im, t) for im, t, _ in ims]
        a, b = g["a"], g["b"]
        steps = int(round((b - a) * fps))
        prev_key = None
        for k in range(steps):
            t = a + k * fr
            key = []
            for im, t_on in ims:
                u = (t - t_on) / ENTER
                al = 0.0 if u <= 0 else (1.0 if u >= 1 else 1 - (1 - u) ** 2)
                bl = 0.0 if u >= 1 else (size * 0.10 * (1 - max(0.0, u)))
                if t > b - EXIT: al *= max(0.0, (b - t) / EXIT)
                key.append((round(al, 2), round(bl, 1)))
            key = tuple(key)
            if key == prev_key and timed:
                timed[-1][2] += fr; continue
            cv = Image.new("RGBA", (W, band), (0, 0, 0, 0))
            for (im, _), (al, bl), (x, y) in zip(ims, key, pos):
                if al <= 0: continue
                s = im.filter(ImageFilter.GaussianBlur(bl)) if bl > 0.3 else im
                if al < 1:
                    arr = np.asarray(s).copy(); arr[:, :, 3] = (arr[:, :, 3] * al).astype(np.uint8)
                    s = Image.fromarray(arr)
                x, y = int(x), int(y); sx, sy = max(0, -x), max(0, -y)
                s = s.crop((sx, sy, min(s.width, W - x), min(s.height, band - y)))
                if s.width > 0 and s.height > 0: cv.alpha_composite(s, (x + sx, y + sy))
            p = os.path.join(work, f"kf{len(timed):05d}.png"); cv.save(p)
            timed.append([t, p, fr]); prev_key = key
    if not timed: return None
    # concat with an exact running clock (same invariant as captions.concat_items)
    items = []; clock = 0.0
    for t, p, d in timed:
        if t > clock + 1e-4: items.append((blank, t - clock)); clock = t
        items.append((p, d)); clock += d
    if total and total > clock: items.append((blank, total - clock))
    lst = os.path.join(work, "kt.txt")
    with open(lst, "w") as f:
        for p, d in items:
            f.write("file '%s'\nduration %.4f\n" % (p.replace("'", "'\\''"), max(0.001, d)))
        f.write("file '%s'\n" % items[-1][0].replace("'", "'\\''"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-r", str(fps), "-c:v", "qtrle", "-pix_fmt", "argb", out], check=True)
    if log:
        log(f"  kinetic title · {len(gs)} group · " +
            " · ".join(f"{g['a']:.1f}s 「{' / '.join(x[0] for x in g['tokens'])}」" for g in gs))
    return out, y_top
