#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Beat type preview (editor 「ပြင်မယ်」 · Visual Plan) ⇒ web/tplprev/beat.<type>.{mp4,jpg}

Remotion `Gallery` (registry `example` · type တိုင်း 3.4s) ကို 480p ဖြင့် တစ်ခါ render ⇒
type တစ်ခုချင်း 256×144 · 3.2s ဖြတ်。 registry ပြောင်းလျှင် ပြန် run。

    python3 tools/beatprev.py [--remo ~/ikki-remotion] [--tmp /Volumes/a/ikki-scratch]
"""
import argparse
import json
import os
import subprocess

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAP = 3.4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remo", default=os.path.expanduser("~/ikki-remotion"))
    ap.add_argument("--tmp", default="/tmp")
    a = ap.parse_args()
    types = list(json.load(open(os.path.join(R, "core", "beat_registry.json"), encoding="utf-8"))["types"])
    g = os.path.join(a.tmp, "beat_gallery_q.mp4")
    subprocess.run(["npx", "remotion", "render", "src/index.ts", "Gallery", g, "--scale=0.25", "--muted",
                    "--crf=24", "--log=error"], cwd=a.remo, check=True)
    out = os.path.join(R, "web", "tplprev")
    os.makedirs(out, exist_ok=True)
    for i, k in enumerate(types):
        t = 0.4 + i * GAP - 0.15
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-t", "3.2", "-i", g,
                        "-vf", "scale=256:144", "-an", "-c:v", "libx264", "-crf", "28", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", os.path.join(out, f"beat.{k}.mp4")], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t + 1.6:.2f}", "-i", g, "-frames:v", "1",
                        "-vf", "scale=256:144", os.path.join(out, f"beat.{k}.jpg")], check=True)
    print(f"beat preview {len(types)} ခု ⇒ {out}")


if __name__ == "__main__":
    main()
