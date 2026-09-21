#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ဂရပ်ဖစ် ဖြစ်ရပ် **အကြံပြုချက်** ထုတ်သည် — အတည်ပြုချက် မဟုတ်ပါ。

⚠️ တိုင်းထားသော စွမ်းဆောင်ရည် (v4 · ground truth ၂၃ ခုနဲ့) —
     lag ၀.၅s  F1 ၆၇% (P ၆၆ · R ၆၈)
     lag ၄.၀s  F1 ၄၈% (P ၈၂ · R ၃၄)
   ⇒ **အလိုအလျောက် မယုံရ**。 spec ရဲ့ 「annotate」အတိုင်း ဖရိန်နဲ့
     လူ/AI က အတည်ပြုမှ dataset ထဲ ထည့်ရမည်。

⚠️ median နောက်ခံ နုတ်နည်း စမ်းပြီး **ပျက်ခဲ့သည်** (F1 ၂၂%) —
   「ပြား」စစ်ချက်က ဂရပ်ဖစ်မဟုတ်ဘဲ ပြောသူကို ဖမ်းမိသည် (၂၀၂၆-၀၉-၂၁)。
"""
import subprocess
import sys

import numpy as np

W, H = 240, 135


def score(path, fps=2.0, lag=1, edge=28, still=5):
    p = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", path, "-vf",
         f"fps={fps},scale={W}:{H}:flags=area,format=gray",
         "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
    n = W * H
    buf, out = [], []
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        f = np.frombuffer(b, np.uint8).astype(np.int16).reshape(H, W)
        buf.append(f)
        if len(buf) > lag + 1:
            buf.pop(0)
        if len(buf) == lag + 1:
            e = np.zeros((H, W), bool)
            e[:, :-1] = np.abs(np.diff(f, axis=1)) > edge
            out.append(float((e & (np.abs(f - buf[0]) <= still)).mean()))
        else:
            out.append(0.0)
    p.stdout.close(); p.wait()
    return np.asarray(out, np.float32), fps


def runs(sc, fps, th=0.025, min_d=1.0, join=1.0):
    """အမှတ် > `th` အပိုင်းများ — `join` စက္ကန့်အတွင်း ကပ်နေလျှင် ပေါင်းသည်"""
    m = sc > th
    out, s = [], None
    for i, v in enumerate(m):
        if v and s is None: s = i
        elif not v and s is not None:
            out.append((s / fps, i / fps)); s = None
    if s is not None:
        out.append((s / fps, len(m) / fps))
    mg = []
    for a, b in out:
        if mg and a - mg[-1][1] <= join:
            mg[-1] = (mg[-1][0], b)
        else:
            mg.append((a, b))
    return [(a, b) for a, b in mg if b - a >= min_d]


if __name__ == "__main__":
    sc, fps = score(sys.argv[1])
    r = runs(sc, fps)
    np.save(sys.argv[2], sc)
    print(f"အကြံပြုချက် {len(r)} ခု")
    for a, b in r:
        print(f"  {a:8.1f} – {b:8.1f}  ({b - a:5.1f}s)")
