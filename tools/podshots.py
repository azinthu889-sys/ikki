#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Podcast reference — shot တစ်ခုချင်းကို **မျက်နှာ အရေအတွက်** နဲ့ ခွဲ + နှုတ်ခမ်း စစ်。

`podref.py` ရဲ့ ထွက် JSON ကို ယူပြီး —
  ① shot တိုင်းရဲ့ အလယ် frame ကို Vision (`tools/mouthcheck`) နဲ့ ဖတ်
     nf 0 ⇒ `broll` · nf ≥2 ⇒ `two` (split / two-shot) · nf 1 ⇒ `single`
  ② single တွေကို color signature k-means (k=2) ⇒ `single_a` / `single_b`
     (host/ဧည့်သည် ဘယ်ဟာလဲ — ပုံကြည့်ပြီး လူက သတ်မှတ်ရ · sheet ထုတ်ပေး)
  ③ class တစ်ခုစီက shot ≤N ခုကို 8fps နဲ့ နှုတ်ခမ်း လှုပ်မှု တိုင်း ⇒ နားထောင်နေ ဝေစု

⚠️ frame ဖိုင်တွေကို `--work` (ပြင်ပ drive) မှာ ထား — Mac disk ~4 GB သာ ကျန်。
⚠️ နှုတ်ခမ်း threshold 0.10 — R3 မှာ bimodal (0.030 vs 0.159) ဖြစ်ခဲ့သည်。

python3 tools/podshots.py VIDEO.mp4 PODREF.json OUT.json --work DIR
"""
import argparse
import json
import os
import shutil
import subprocess

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MC = os.path.join(HERE, "mouthcheck")
LIP_THR = 0.10


def vision(d):
    p = subprocess.run([MC, d], capture_output=True, text=True)
    return {j["f"]: j for j in (json.loads(l) for l in p.stdout.splitlines() if l.startswith("{"))}


def kmeans2(X, it=50, seed=0):
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), 2, replace=False)]
    for _ in range(it):
        lab = np.argmin(((X[:, None] - C[None]) ** 2).sum(-1), 1)
        C = np.array([X[lab == k].mean(0) if (lab == k).any() else C[k] for k in range(2)])
    return lab


def stats(v):
    v = np.asarray(v, float)
    if not len(v):
        return {"n": 0}
    return {"n": int(len(v)), "median": round(float(np.median(v)), 2),
            "p25": round(float(np.percentile(v, 25)), 2),
            "p75": round(float(np.percentile(v, 75)), 2),
            "max": round(float(v.max()), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("podref")
    ap.add_argument("out")
    ap.add_argument("--work", required=True)
    ap.add_argument("--lip_n", type=int, default=30)
    ap.add_argument("--body_from", type=float, default=300.0)
    a = ap.parse_args()
    r = json.load(open(a.podref))
    sig = np.load(a.podref.rsplit(".", 1)[0] + "_sig.npy")
    sh = r["shots"]
    wd = os.path.join(a.work, "mid")
    shutil.rmtree(wd, ignore_errors=True)
    os.makedirs(wd)
    # ⚠️ shot တစ်ခုချင်း seek ⇒ R3 မှာ ၁၆.၅ မိနစ် ⇒ **တစ်ကြိမ်တည်း decode** (2fps) ပြီး
    #    အလယ်နဲ့ အနီးဆုံး frame ကို ရွေး
    ad = os.path.join(a.work, "all")
    shutil.rmtree(ad, ignore_errors=True)
    os.makedirs(ad)
    subprocess.run(["ffmpeg", "-v", "error", "-threads", "0", "-i", a.video, "-vf",
                    "fps=2,scale=640:-2", "-q:v", "5", os.path.join(ad, "%06d.jpg")])
    nall = len(os.listdir(ad))
    for i, s in enumerate(sh):
        k = min(nall, max(1, int(round((s["t0"] + s["t1"]) / 2 * 2)) + 1))
        shutil.copyfile(os.path.join(ad, f"{k:06d}.jpg"), os.path.join(wd, f"{i:05d}.jpg"))
    shutil.rmtree(ad, ignore_errors=True)
    V = vision(wd)
    for i, s in enumerate(sh):
        j = V.get(f"{i:05d}.jpg", {"nf": 0})
        s["nf"] = j["nf"]
        s["cls"] = "broll" if j["nf"] == 0 else ("two" if j["nf"] >= 2 else "single")
    si = [i for i, s in enumerate(sh) if s["cls"] == "single"]
    if len(si) >= 4:
        X = sig[si].reshape(len(si), -1)
        for i, k in zip(si, kmeans2(X)):
            sh[i]["cls"] = "single_" + "ab"[k]
    # ③ နှုတ်ခမ်း
    rng = np.random.default_rng(1)
    lip = {}
    for c in ["single_a", "single_b", "two"]:
        pool = [i for i, s in enumerate(sh) if s["cls"] == c
                and s["t1"] - s["t0"] >= 2 and s["t0"] >= a.body_from]
        if not pool:
            continue
        pick = rng.choice(pool, min(a.lip_n, len(pool)), replace=False)
        ld = os.path.join(a.work, "lip")
        shutil.rmtree(ld, ignore_errors=True)
        os.makedirs(ld)
        for k, i in enumerate(pick):
            s = sh[i]
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s['t0'] + 0.2:.3f}", "-i", a.video,
                            "-t", f"{min(6, s['t1'] - s['t0'] - 0.4):.3f}", "-vf", "fps=8,scale=960:-2",
                            "-q:v", "4", os.path.join(ld, f"s{k:03d}_%03d.jpg")])
        LV = vision(ld)
        per = {}
        for f, j in LV.items():
            per.setdefault(int(f[1:4]), []).append(j["open"])
        mv = [float(np.abs(np.diff([x for x in v if x >= 0])).mean())
              for v in per.values() if sum(x >= 0 for x in v) >= 8]
        if mv:
            lip[c] = {"n": len(mv), "median": round(float(np.median(mv)), 3),
                      "listening": round(float(np.mean(np.array(mv) < LIP_THR)), 2)}
        shutil.rmtree(ld, ignore_errors=True)
    # ④ စုစည်း
    body = [s for s in sh if s["t0"] >= a.body_from]
    tot = sum(s["t1"] - s["t0"] for s in body) or 1
    cls = {}
    for c in sorted({s["cls"] for s in sh}):
        L = [s["t1"] - s["t0"] for s in body if s["cls"] == c]
        cls[c] = {"share": round(sum(L) / tot, 3), "len": stats(L), "lip": lip.get(c)}
    per_min = [sum(1 for s in sh if m * 60 <= s["t0"] < (m + 1) * 60) for m in range(8)]
    body_min = (r["dur"] - a.body_from) / 60
    trans = {}
    for x, y in zip(body, body[1:]):
        k = "->".join(sorted([x["cls"], y["cls"]]))
        trans[k] = trans.get(k, 0) + 1
    res = {"src": a.video, "dur": r["dur"], "cuts": r["cuts"],
           "body_cuts_per_min": round(len(body) / body_min, 2) if body_min > 0 else None,
           "first8min_cuts": per_min, "classes": cls,
           "transitions": dict(sorted(trans.items(), key=lambda x: -x[1])[:8])}
    json.dump({"summary": res, "shots": sh}, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    # sheet — single_a / single_b / two / broll ၃ ပုံစီ (host/ဧည့်သည် လူက သတ်မှတ်ရန်)
    rows = []
    for c in ["single_a", "single_b", "two", "broll"]:
        ids = [i for i, s in enumerate(sh) if s["cls"] == c]
        for k in range(4):
            rows.append(os.path.join(wd, f"{ids[int(k * (len(ids) - 1) / 3)]:05d}.jpg") if ids else None)
    blank = os.path.join(a.work, "blank.jpg")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=black:s=640x360",
                    "-frames:v", "1", blank])
    sd = os.path.join(a.work, "sheet")
    shutil.rmtree(sd, ignore_errors=True)
    os.makedirs(sd)
    for k, p in enumerate(rows):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p or blank, "-vf",
                        "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2",
                        os.path.join(sd, f"{k:03d}.png")])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(sd, "%03d.png"), "-vf", "tile=4x4",
                    "-frames:v", "1", a.out.rsplit(".", 1)[0] + "_sheet.jpg"])
    shutil.rmtree(wd, ignore_errors=True)
    shutil.rmtree(sd, ignore_errors=True)


if __name__ == "__main__":
    main()
