#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""နောက်ခံ သီချင်း catalog ဆောက်ခြင်း (Music audit P0 အချက် ၁)

⚠️ `music.pick()` က ကိုက်ညီသော **ပထမဖိုင်ကို** ပြန်ပေးသည် ⇒ ဗီဒီယို
   အားလုံး သီချင်းတစ်ပုဒ်တည်း ရနိုင်သည်。 metadata (BPM · အား · loop
   နေရာ · လိုင်စင်) မရှိသဖြင့် ရွေးချယ်မှုကို ပိုကောင်းအောင် မလုပ်နိုင်ပါ。
⚠️ `aloop` က သီချင်းတိုင်း သပ်သပ်ရပ်ရပ် ကျော့သည် ဟု **ယူဆ**ထားသည် —
   တကယ် ကျော့မှတ်မှာ ကျိုးသလား ဘယ်တော့မှ မတိုင်းခဲ့ပါ。
   ⇒ ဤ tool က ကျော့မှတ်ကို **တိုင်း**ပြီး catalog ထဲ မှတ်သည်。

tag တိုင်းကို sample ကနေ တိုင်းယူသည် — မှန်းဆချက် မဟုတ်。
"""
import json
import os
import re
import subprocess
import sys

import numpy as np

SR = 22050


def pcm(path, sr=SR, mono=True):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path,
                        "-ac", "1" if mono else "2", "-ar", str(sr),
                        "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, "<f4").astype(np.float64)


def loud(path):
    """`(LUFS-I, dBTP)` — ffmpeg loudnorm ကနေ"""
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                        "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = re.search(r"\{[^{}]*input_i[^{}]*\}", e, re.S)
    if not m:
        return None, None
    d = json.loads(m.group(0))
    return float(d.get("input_i", 0)), float(d.get("input_tp", 0))


def bpm(x, sr=SR):
    """onset autocorrelation ကနေ BPM — မသေချာလျှင် `None`

    ⚠️ BPM ကို **မှန်းဆ မရေးရ**。 ယုံကြည်မှု နည်းလျှင် `None` ပြန်ပေးသည် —
       မှားသော BPM က ရွေးချယ်မှုကို မှားစေသည်。
    """
    n = 1024
    h = 256
    if len(x) < sr * 10:
        return None, 0.0
    f = np.abs(np.fft.rfft(x[:len(x) // h * h - n].reshape(-1, h)[:, :]
                           if False else
                           np.lib.stride_tricks.sliding_window_view(x, n)[::h]
                           * np.hanning(n), axis=1))
    flux = np.maximum(0, np.diff(f, axis=0)).sum(1)
    flux = flux - flux.mean()
    if not flux.any():
        return None, 0.0
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    fps = sr / h
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 60)     # 60–180 BPM
    if hi >= len(ac) or lo >= hi:
        return None, 0.0
    seg = ac[lo:hi]
    k = int(np.argmax(seg)) + lo
    conf = float(seg.max() / (ac[0] + 1e-9))
    return round(60.0 * fps / k, 1), round(conf, 3)


def seam(x, sr=SR, win=0.25):
    """ကျော့မှတ် (အဆုံး→အစ) ရဲ့ **ကျိုးမှု** — dB ကွာဟမှု · နိမ့်လေ ကောင်းလေ

    ⚠️ `aloop` က ဖိုင် အဆုံးကနေ အစကို တိုက်ရိုက် ဆက်သည် ⇒ အဆုံးက
       တိတ်ပြီး အစက ကျယ်လျှင် **ထိုးကျသံ** ကြားရသည်。
    """
    w = int(sr * win)
    if len(x) < w * 4:
        return None
    a = float(np.sqrt((x[-w:] ** 2).mean()))
    b = float(np.sqrt((x[:w] ** 2).mean()))
    return round(abs(20 * np.log10((a + 1e-9) / (b + 1e-9))), 2)


def loop_region(x, sr=SR, head=4.0, tail=4.0, win=0.5):
    """**အတည်ပြု ကျော့နယ်** `(စ, ဆုံး)` — ဝင်/ထွက် အား အနီးဆုံး နေရာ

    ⚠️ intro/outro ကို ဖယ်ပြီး ကျော့သည် — အဲဒါက ကျော့မှတ် ကျိုးမှုကို
       အများဆုံး လျှော့သည်。
    """
    d = len(x) / sr
    if d < head + tail + 8:
        return None
    w = int(sr * win)
    best, bs = None, 1e9
    for s in np.arange(head, min(head + 8, d / 3), 0.5):
        for e in np.arange(max(d - tail - 8, d * 0.6), d - tail, 0.5):
            if e - s < 8:
                continue
            a = float(np.sqrt((x[int(e * sr) - w:int(e * sr)] ** 2).mean()))
            b = float(np.sqrt((x[int(s * sr):int(s * sr) + w] ** 2).mean()))
            g = abs(20 * np.log10((a + 1e-9) / (b + 1e-9)))
            if g < bs:
                bs, best = g, (round(float(s), 2), round(float(e), 2))
    return (best[0], best[1], round(bs, 2)) if best else None


MOOD = {
    "ZAE_house_bed":       dict(mood="brand", energy=0.6, voice_ok=True,
                                baked_fx=True, license="ZAE house — ကိုယ်ပိုင်"),
    "Beauty Flow":         dict(mood="calm", energy=0.35, voice_ok=True,
                                license="Kevin MacLeod · CC BY 3.0"),
    "Kevin MacLeod Wallpaper": dict(mood="corporate", energy=0.45, voice_ok=True,
                                    license="Kevin MacLeod · CC BY 3.0"),
    "4604 Wallpaper By Kevin Macleod": dict(mood="corporate", energy=0.45,
                                            voice_ok=True,
                                            license="Kevin MacLeod · CC BY 3.0"),
    "5759 Blippy Trance By Kevin Macleod": dict(mood="upbeat", energy=0.7,
                                                voice_ok=True,
                                                license="Kevin MacLeod · CC BY 3.0"),
}


def build(d, out):
    items = []
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith((".m4a", ".mp3", ".wav")):
            continue
        p = os.path.join(d, f)
        x = pcm(p)
        if not len(x):
            continue
        tid = os.path.splitext(f)[0]
        li, tp = loud(p)
        b, bc = bpm(x)
        lr = loop_region(x)
        meta = dict(MOOD.get(tid, {}))
        items.append(dict(
            id=tid, file=f, version=1,
            dur=round(len(x) / SR, 2),
            lufs=li, true_peak=tp,
            bpm=b if (bc or 0) >= 0.12 else None,
            bpm_conf=bc,
            seam_db=seam(x),
            loop=dict(start=lr[0], end=lr[1], seam_db=lr[2]) if lr else None,
            mood=meta.get("mood", "unknown"),
            energy=meta.get("energy"),
            voice_ok=meta.get("voice_ok", True),
            baked_fx=meta.get("baked_fx", False),
            license=meta.get("license", "⚠️ မမှတ်ရသေး"),
            measured=["dur", "lufs", "true_peak", "bpm", "seam_db", "loop"]))
    doc = dict(version=1, n=len(items),
               _doc="⚠️ `mood`/`energy`/`license` က **လက်နဲ့ မှတ်ထား** — "
                    "ကျန်အားလုံးကို sample ကနေ တိုင်းယူသည်。 "
                    "`bpm` က ယုံကြည်မှု ၀.၁၂ အောက်ဆိုလျှင် `null`。",
               items=items)
    with open(out, "w", encoding="utf-8") as g:
        json.dump(doc, g, ensure_ascii=False, indent=1)
    return doc


if __name__ == "__main__":
    d = sys.argv[1]
    o = sys.argv[2] if len(sys.argv) > 2 else os.path.join(d, "catalog.json")
    doc = build(d, o)
    print(f"music catalog · {doc['n']} ပုဒ်")
    for it in doc["items"]:
        lp = it["loop"]
        print(f"  {it['id'][:34]:34} {it['dur']:6.1f}s  "
              f"{it['lufs'] if it['lufs'] is not None else 0:6.1f} LUFS  "
              f"TP {it['true_peak'] if it['true_peak'] is not None else 0:5.1f}  "
              f"BPM {str(it['bpm']):>5}  ကျော့ကျိုး {it['seam_db']:5.1f} dB"
              + (f"  → နယ် {lp['start']}–{lp['end']}s ({lp['seam_db']} dB)" if lp else ""))
