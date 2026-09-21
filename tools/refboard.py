#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motion Kit Step 1 — reference ဗီဒီယိုကနေ **calibration dataset** ထုတ်သည်。

⚠️ spec §10 Step 1 — 「Do not use broad statements such as 'premium' as a
   design specification」⇒ ဖြစ်ရပ်တစ်ခုချင်းကို **အချိန်နဲ့ ကိန်းနဲ့** မှတ်ရမည်。

⚠️ အဓိက ရည်ရွယ်ချက် — `tokens.json` ရဲ့ `motion` (micro/enter/settle/exit) က
   ယခု `src: "spec"` ဖြစ်နေသည် (**မတိုင်းရသေး**)。 ဒီတူးလ်က အဲဒါကို
   `measured` ဖြစ်အောင် လုပ်ပေးသည်。

နည်းလမ်း — ဖြစ်ရပ်ဝင်းဒိုးကို **native fps** နဲ့ ဖတ်ပြီး မင်ပမာဏ လမ်းကြောင်း
ဆွဲသည်。 ဝင်ချိန် = ၅% → ၉၅% · ငြိမ်ချိန် = ၉၅% အထက် · ထွက်ချိန် = ၉၅% → ၅%。
"""
import json
import os
import subprocess
import sys

import numpy as np

W, H = 240, 135


def strip(path, t0, t1, fps):
    """ဝင်းဒိုးတစ်ခုကို native fps နဲ့ ဖတ် → (n, H, W, 3) float32"""
    n = max(1, int(round((t1 - t0) * fps)))
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t0):.3f}",
         "-i", path, "-t", f"{t1 - t0:.3f}", "-vf",
         f"fps={fps},scale={W}:{H}:flags=area,format=rgb24",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8)
    k = len(a) // (W * H * 3)
    if k < 2:
        return None
    return a[:k * W * H * 3].astype(np.float32).reshape(k, H, W, 3)


def ink(fr, mode="gold"):
    """frame တစ်ခုချင်းရဲ့ မင်ပမာဏ — ဂရပ်ဖစ် ရှိမရှိ အညွှန်း"""
    r, g, b = fr[..., 0], fr[..., 1], fr[..., 2]
    if mode == "gold":
        m = (r > 170) & (g > 140) & (b < 45) & (r - b > 150)
    else:                       # အဖြူ/အလင်း စာသား
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        m = lum > 200
    return m.reshape(len(fr), -1).mean(1)


def phases(y, fps, lo=0.05, hi=0.95):
    """မင်လမ်းကြောင်း → `(enter, settle, exit, peak_at)` စက္ကန့်

    ⚠️ ဆူညံသံကို ဖယ်ရန် ၃ frame ချောမွေ့စေသည် — မချောမွေ့လျှင်
       frame တစ်ခုတည်းရဲ့ ခုန်မှုက ဝင်ချိန်ကို ၀ ဖြစ်စေမည်。
    """
    if y is None or len(y) < 4:
        return None
    k = np.convolve(y, np.ones(3) / 3.0, "same")
    pk = float(k.max())
    if pk <= 1e-6:
        return None
    n = k / pk
    on = np.nonzero(n >= hi)[0]
    if not len(on):
        return None
    i_hi0, i_hi1 = int(on[0]), int(on[-1])
    pre = np.nonzero(n[:i_hi0 + 1] <= lo)[0]
    i_lo0 = int(pre[-1]) if len(pre) else 0
    post = np.nonzero(n[i_hi1:] <= lo)[0]
    i_lo1 = i_hi1 + int(post[0]) if len(post) else len(n) - 1
    return (round((i_hi0 - i_lo0) / fps, 3),
            round((i_hi1 - i_hi0) / fps, 3),
            round((i_lo1 - i_hi1) / fps, 3),
            round(i_hi0 / fps, 3))


def centroid(fr, mode="gold"):
    """မင်ရဲ့ အလယ်မှတ် (x, y) အချိုး — ရွေ့လျားမှု ခွဲခြားရန်"""
    r, g, b = fr[..., 0], fr[..., 1], fr[..., 2]
    if mode == "gold":
        m = (r > 170) & (g > 140) & (b < 45) & (r - b > 150)
    else:
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        m = lum > 200
    out = []
    ys, xs = np.mgrid[0:fr.shape[1], 0:fr.shape[2]]
    for i in range(len(fr)):
        s = m[i].sum()
        if s < 8:
            out.append((None, None)); continue
        out.append((round(float((xs * m[i]).sum() / s / fr.shape[2]), 4),
                    round(float((ys * m[i]).sum() / s / fr.shape[1]), 4)))
    return out


def event(path, t0, t1, fps, mode="gold", pad=0.8):
    """ဖြစ်ရပ်တစ်ခု တိုင်းသည် → dict · မရလျှင် None"""
    fr = strip(path, max(0.0, t0 - pad), t1 + pad, fps)
    if fr is None:
        return None
    y = ink(fr, mode)
    ph = phases(y, fps)
    if not ph:
        return None
    enter, settle, exit_, peak = ph
    cs = centroid(fr, mode)
    seen = [c for c in cs if c[0] is not None]
    move = None
    if len(seen) >= 2:
        move = (round(seen[-1][0] - seen[0][0], 4),
                round(seen[-1][1] - seen[0][1], 4))
    return dict(t=round(max(0.0, t0 - pad) + peak, 2),
                enter=enter, settle=settle, exit=exit_,
                peak_ink=round(float(y.max()), 5), move=move, fps=fps)


if __name__ == "__main__":
    print(json.dumps(event(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]),
                           float(sys.argv[4])), ensure_ascii=False))
