# -*- coding: utf-8 -*-
"""Designed camera moves for short-916 (Zin 2026-09-27, from reference r3).

r3 measured (reports/zae_short_r3_layers_2026-09-27.md): 7 designed moves in
42 s -- push-in +53 %/0.9 s at the open, zoom-in +18 %/1.0 s, pull-out
-26 %/1.4 s at the close, zoom-outs -8..-11 % -- mostly **ease-out** (share of
the move done in its first half 0.80-0.97). IKKI had none, only a slow
breathing zoom.

For a talking head the zoom alternates between the shot as framed (1.00) and
a punched-in level, capped at 1.20 (the 2560x1440 proxy's 9:16 crop is
already 1.33x upscaled). Moves land on sentence starts, never inside B-roll or
a graphic (both cover the frame, so the move would be invisible or fight the
card), and at least `gap` s apart.

Rendering is done per frame with a single PIL resample from the native crop,
so there is no integer-pixel jitter (ffmpeg zoompan rounds x/y per frame).
"""
import math, subprocess
import numpy as np

ZMAX = 1.20

def _ease(u, kind):
    u = min(1.0, max(0.0, u))
    if kind == "expo":                      # the open: very front-loaded (r3 share 0.97)
        return 1.0 if u >= 1 else 1 - 2 ** (-10 * u)
    return 1 - (1 - u) ** 3                 # cubic ease-out (share 0.875)

def plan(dur, caps, avoid, gap=5.5, z_in=1.16, first=0.9, move=0.9, pull=1.2, outro=1.4):
    """-> [(t, d, z0, z1, ease)] on the cut timeline.
    caps: [{start, end}] sentence starts; avoid: [(a, b)] B-roll / graphic windows."""
    z_in = min(ZMAX, z_in)
    def blocked(t, d):
        return any(not (t + d + 0.3 <= a or t - 0.3 >= b) for a, b in avoid)
    moves = []; z = 1.0
    if dur > 3 and not blocked(0.0, first):
        moves.append((0.0, first, 1.0, z_in, "expo")); z = z_in
    starts = sorted(float(c["start"]) for c in caps if c.get("start") is not None)
    last = moves[-1][0] + moves[-1][1] if moves else -9
    end_t = max(0.0, dur - outro - 0.4)
    for t in starts:
        if t - last < gap or t >= end_t - gap * 0.5: continue
        zn = 1.0 if z > 1.0 else z_in
        d = pull if zn < z else move
        if blocked(t, d): continue
        moves.append((round(t, 3), d, z, zn, "cubic")); z = zn; last = t + d
    # the close: pull out (push in first if we sit at 1.00 and there is room)
    if dur > 6:
        t = round(end_t, 3)
        if z == 1.0 and t - last >= gap and not blocked(t - move - 0.2, move):
            moves.append((round(t - move - 0.2, 3), move, 1.0, z_in, "cubic")); z = z_in
        if z > 1.0 and not blocked(t, outro):
            moves.append((t, outro, z, 1.0, "cubic")); z = 1.0
    return moves

def zoom_at(t, moves):
    z = 1.0
    for t0, d, z0, z1, e in moves:
        if t < t0: break
        z = z0 + (z1 - z0) * _ease((t - t0) / d, e)
    return z

def render(src, out, fps, moves, W, H, pivot=(0.5, 0.40), log=None):
    """src (cut video, any aspect) -> out WxH, centre-cropped to W:H then zoomed
    about `pivot` (0-1 of the crop). Audio copied untouched."""
    from PIL import Image
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                         "stream=width,height", "-of", "csv=p=0", src], capture_output=True, text=True)
    sw, sh = [int(x) for x in pr.stdout.strip().split(",")[:2]]
    cw = min(sw, int(sh * W / H) // 2 * 2); ch = min(sh, int(sw * H / W) // 2 * 2)
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf",
                           f"crop={cw}:{ch},fps={fps}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-i", src,
                           "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-preset", "veryfast",
                           "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", out],
                          stdin=subprocess.PIPE)
    px, py = pivot[0] * cw, pivot[1] * ch
    n = 0; fb = cw * ch * 3; zs = []
    try:
        while True:
            b = rd.stdout.read(fb)
            if len(b) < fb: break
            z = zoom_at(n / fps, moves); zs.append(z)
            im = Image.frombytes("RGB", (cw, ch), b)
            # output pixel (X, Y) samples source at pivot + (X/W*cw - px)/z  (inverse map)
            a = cw / W / z; e = ch / H / z
            c = px - px / z; f = py - py / z
            # keep the window inside the crop
            c = min(max(c, 0.0), cw - cw / z); f = min(max(f, 0.0), ch - ch / z)
            wr.stdin.write(im.transform((W, H), Image.AFFINE, (a, 0, c, 0, e, f), Image.BICUBIC).tobytes())
            n += 1
    finally:
        wr.stdin.close(); wr.wait(); rd.kill()
    if wr.returncode != 0:
        raise RuntimeError(f"camove encode failed ({wr.returncode})")
    if log:
        log(f"  camera move · {len(moves)} ခု · zoom {min(zs or [1]):.2f}–{max(zs or [1]):.2f}× · "
            f"pivot ({pivot[0]:.2f},{pivot[1]:.2f}) · " +
            " ".join(f"{t:.1f}s {z0:.2f}→{z1:.2f}/{d:.1f}s" for t, d, z0, z1, _ in moves))
    return out

def pivot_from_pose(frames, sw=16, sh=9, W=9, H=16):
    """median face centre (source 0-1, y from top) -> 0-1 of the centre W:H crop"""
    fr = [f for f in (frames or []) if f.get("nf") and f.get("fx", -1) >= 0]
    if len(fr) < 5: return (0.5, 0.40)
    fx = float(np.median([f["fx"] for f in fr])); fy = float(np.median([f["fy"] for f in fr]))
    cwf = min(1.0, (H and (sh * W / H) / sw))           # crop width as a fraction of source width
    x = (fx - (1 - cwf) / 2) / cwf
    return (min(0.8, max(0.2, x)), min(0.6, max(0.2, fy)))
