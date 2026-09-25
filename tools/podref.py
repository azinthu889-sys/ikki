#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Podcast reference တိုင်းတာ — ဖြတ်ချက် · ကင်မရာ ထောင့် · shot အရှည်。

⚠️ multicam podcast ရဲ့ ကင်မရာ ထောင့်တွေက **ပုံသေ** ⇒ shot တစ်ခုချင်းရဲ့
   ပုံသေး (32×18 grayscale) ကို cluster လုပ်လျှင် ထောင့်တစ်ခု = cluster တစ်ခု。
⚠️ ပျမ်းမျှ တစ်ခုတည်း မပြ — n · median · p25/p75 · min/max · sd
   ([[measure-distribution-rule]])。

python3 tools/podref.py REF.mp4 OUT.json
"""
import json
import subprocess
import sys

import numpy as np

SW, SH, FPS = 64, 36, 8   # scan grid · scan fps (24fps ⇒ 3 frame တစ်ခါ)


def scan(path):
    """8fps · 64×36 gray frames ⇒ (n, SH, SW) uint8"""
    p = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-threads", "0", "-i", path,
         "-vf", f"fps={FPS},scale={SW}:{SH}:flags=area,format=gray",
         "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    buf = p.stdout.read()
    p.wait()
    a = np.frombuffer(buf, np.uint8)
    return a[: len(a) // (SW * SH) * SW * SH].reshape(-1, SH, SW)


def cuts(fr, thr=0.35):
    """histogram + pixel diff နှစ်ခုလုံး ကျော်မှ ဖြတ်ချက် (ကင်မရာ ရွေ့/လက်ဟန် မပါ)"""
    f = fr.astype(np.float32) / 255.0
    pix = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    h = np.stack([np.histogram(x, 16, (0, 1))[0] for x in f]).astype(np.float32)
    h /= h.sum(1, keepdims=True)
    hd = 0.5 * np.abs(np.diff(h, axis=0)).sum(1)
    score = pix / (np.median(pix) + 1e-6)
    idx = [i + 1 for i in range(len(pix))
           if score[i] > 6 and hd[i] > thr * 0.5 and pix[i] > 0.06]
    out = []
    for i in idx:                       # ၂ frame အတွင်း ထပ် ⇒ တစ်ခု
        if not out or i - out[-1] > 2:
            out.append(i)
    return out


def stats(v):
    v = np.asarray(v, float)
    if not len(v):
        return {"n": 0}
    return {"n": int(len(v)), "median": round(float(np.median(v)), 2),
            "p25": round(float(np.percentile(v, 25)), 2),
            "p75": round(float(np.percentile(v, 75)), 2),
            "min": round(float(v.min()), 2), "max": round(float(v.max()), 2),
            "sd": round(float(v.std()), 2)}


def cluster(sig, tol=0.055):
    """greedy — ပုံသေး L1 အကွာ < tol ⇒ ထောင့်တူ"""
    cent, lab = [], []
    for s in sig:
        d = [np.abs(s - c).mean() for c in cent]
        if d and min(d) < tol:
            k = int(np.argmin(d))
            lab.append(k)
            cent[k] = cent[k] * 0.9 + s * 0.1
        else:
            cent.append(s.copy())
            lab.append(len(cent) - 1)
    return lab


def main(src, out):
    fr = scan(src)
    dur = len(fr) / FPS
    cs = cuts(fr)
    bounds = [0] + cs + [len(fr)]
    shots = []
    for a, b in zip(bounds, bounds[1:]):
        if b - a < 1:
            continue
        mid = fr[a + (b - a) // 4: b - (b - a) // 4 or b].astype(np.float32) / 255
        shots.append({"t0": round(a / FPS, 3), "t1": round(b / FPS, 3),
                      "sig": (mid.mean(0) if len(mid) else fr[a] / 255.0)})
    lab = cluster([s["sig"] for s in shots])
    np.save(out.rsplit(".", 1)[0] + "_sig.npy",
            np.stack([s["sig"] for s in shots]).astype(np.float32))
    for s, k in zip(shots, lab):
        s["cam"] = k
        del s["sig"]
    lens = [s["t1"] - s["t0"] for s in shots]
    cam = {}
    for s in shots:
        c = cam.setdefault(s["cam"], {"n": 0, "sec": 0.0, "lens": []})
        c["n"] += 1
        c["sec"] += s["t1"] - s["t0"]
        c["lens"].append(s["t1"] - s["t0"])
    cams = sorted(({"cam": k, "n": v["n"], "share": round(v["sec"] / dur, 4),
                    "len": stats(v["lens"]), "first": next(
                        s["t0"] for s in shots if s["cam"] == k)}
                   for k, v in cam.items()), key=lambda x: -x["share"])
    # ၅ မိနစ် ဝင်းဒိုးအလိုက် ဖြတ်နှုန်း — cold open / အလယ် / အဆုံး ကွာမကွာ
    win = [sum(1 for c in cs if w * 300 <= c / FPS < (w + 1) * 300) / 5.0
           for w in range(int(dur // 300) + 1)]
    res = {"src": src, "dur": round(dur, 1), "scan_fps": FPS,
           "cuts": len(cs), "cuts_per_min": round(len(cs) / dur * 60, 2),
           "shot_len": stats(lens), "cams": cams,
           "cuts_per_min_by_5min": win, "shots": shots}
    json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "shots"},
                     ensure_ascii=False, indent=1)[:4000])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
