#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ဗီဒီယိုပေါ် **ထပ်တင်ထားသော ဂရပ်ဖစ်** ရှာခြင်း — အရောင် မမှီခို。

⚠️ အရောင်နဲ့ ရှာလျှင် ပုံစံတစ်ခုတည်းသာ မိသည် (v4 ရဲ့ အဝါ)。 v2 ရဲ့ အဖြူ
   ခေါင်းစဉ်ကတ် · v5 ရဲ့ ဘေးဘောင် ကတ်တွေ လွတ်သွားခဲ့သည် (၂၀၂၆-၀၉-၂၁)。
⚠️ ယခင် 「အချိန်နဲ့ မရွေ့သော အနား」နည်းက precision ၇၁–၈၁% သာ ရခဲ့သည် —
   မယုံလောက်ပါ。

နည်းလမ်း — **အချိန်ဆိုင်ရာ median နောက်ခံ နုတ်ခြင်း**。 ဝင်းဒိုးတစ်ခုအတွင်း
pixel တစ်ခုချင်းရဲ့ median က 「နောက်ခံ」ဖြစ်ပြီး ထပ်တင်ထားသော ဂရပ်ဖစ်က
အဲဒါနဲ့ **ကွဲပြီး ဆက်တိုက် ကွဲနေ**သည် (ပြောသူက ရွေ့သဖြင့် median သို့
ပြန်ကျသည်)。
"""
import subprocess
import sys

import numpy as np

W, H = 192, 108


def gray(path, fps=2.0):
    p = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", path, "-vf",
         f"fps={fps},scale={W}:{H}:flags=area,format=gray",
         "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
    n = W * H
    out = []
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        out.append(np.frombuffer(b, np.uint8).reshape(H, W))
    p.stdout.close(); p.wait()
    return np.asarray(out, np.int16) if out else None


def score(fr, win=9, dev=34, flat=9):
    """frame တစ်ခုချင်းရဲ့ 「ထပ်တင် ဂရပ်ဖစ်」အမှတ် (၀–၁)

    `win`  — median ဝင်းဒိုး (frame · 2Hz ⇒ ၉ = ၄.၅s)
    `dev`  — နောက်ခံနဲ့ ဘယ်လောက် ကွာမှ ထပ်တင်ဟု ယူမလဲ
    `flat` — ထပ်တင်က **ပြားသည်** (ဘေးချင်း ကွာဟမှု နည်း) — ရုပ်က မပြား
    """
    if fr is None or len(fr) < win + 2:
        return None
    n = len(fr)
    half = win // 2
    out = np.zeros(n, np.float32)
    for i in range(n):
        a = max(0, i - half); b = min(n, i + half + 1)
        bg = np.median(fr[a:b], axis=0)
        d = np.abs(fr[i] - bg) > dev
        g = np.zeros((H, W), bool)
        g[:, :-1] = np.abs(np.diff(fr[i].astype(np.int16), axis=1)) < flat
        out[i] = float((d & g).mean())
    return out


def runs(sc, fps, th, min_d=0.6):
    m = sc > th
    out = []; s = None
    for i, v in enumerate(m):
        if v and s is None: s = i
        elif not v and s is not None:
            if (i - s) / fps >= min_d: out.append((s / fps, i / fps))
            s = None
    if s is not None and (len(m) - s) / fps >= min_d:
        out.append((s / fps, len(m) / fps))
    return out


if __name__ == "__main__":
    f = gray(sys.argv[1], 2.0)
    s = score(f)
    np.save(sys.argv[2], s)
    print(f"  frame {len(s)} · p50 {np.percentile(s,50)*100:.3f}% "
          f"p90 {np.percentile(s,90)*100:.3f}% p99 {np.percentile(s,99)*100:.3f}%")
