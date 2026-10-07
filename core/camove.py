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
import math, re, subprocess
import numpy as np

ZMAX = 1.20

def _ease(u, kind):
    u = min(1.0, max(0.0, u))
    if kind == "expo":                      # the open: very front-loaded (r3 share 0.97)
        return 1.0 if u >= 1 else 1 - 2 ** (-10 * u)
    if kind == "inout":                     # the return to 1.00: no jolt at either end
        return 0.5 - 0.5 * math.cos(math.pi * u)
    return 1 - (1 - u) ** 3                 # cubic ease-out (share 0.875)

# Zin 2026-09-27: "a zoom in/out now and then" is liked, "staying zoomed" is not.
# => the base is always 1.00x; every move is a round trip: in -> hold -> back.
#    Gates (from his words, provisional -- not measured on a reference):
#    G10 every move returns to 1.00 (+-0.005) · G11 > 1.02 for <= 3.0 s at a
#    stretch · G12 > 1.02 for <= 20 % of the video (planned against 18 %).
IN_D, HOLD, OUT_D = 0.8, 1.0, 1.0

def plan(dur, caps, avoid, gap=5.5, z_in=1.16, budget=0.18, open_=True):
    """-> [(t, d, z0, z1, ease)] on the cut timeline, in/out pairs.
    caps: [{start, end}] sentence starts; avoid: [(a, b)] B-roll / graphic windows."""
    z_in = min(ZMAX, z_in)
    span = IN_D + HOLD + OUT_D
    def blocked(t):
        return any(not (t + span + 0.3 <= a or t - 0.3 >= b) for a, b in avoid)
    starts = sorted(float(c["start"]) for c in caps if c.get("start") is not None)
    if open_ and dur > span + 1: starts = [0.0] + [t for t in starts if t > 0.05]
    moves = []; last = -9.0; used = 0.0
    for t in starts:
        if t - last < gap or t + span > dur - 0.2 or blocked(t): continue
        if used + span > budget * dur: break
        e = "expo" if t == 0.0 else "cubic"
        moves.append((round(t, 3), IN_D, 1.0, z_in, e))
        moves.append((round(t + IN_D + HOLD, 3), OUT_D, z_in, 1.0, "inout"))
        last = t + span; used += span
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
    # ⚠️ side data (rotation matrix) ပါသော ဖိုင်မှာ csv က `1440\n\n2560` ပုံစံ ထွက် ⇒ ကိန်း ၂ လုံးကိုသာ ယူ
    #    (Raw.mp4 · j_4dd59bb90b5a · ၂၀၂၆-၁၀-၀၇ — camera move ကျ ⇒ breathing zoom ဖြစ်ခဲ့)
    sw, sh = [int(x) for x in re.findall(r"\d+", pr.stdout)[:2]]
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
