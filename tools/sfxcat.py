#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SFX asset catalog ဆောက်ခြင်း (SFX spec P1)

⚠️ `sfxlib.ROLE` က role ၂၂ ခုစလုံးကို **ဖိုင်တစ်ခုတည်း** ညွှန်းထားသည် —
   ၄၉၇ ဖိုင် ရှိပါလျက် (၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့)。 ⇒ တူညီသော whoosh/click
   ထပ်ကာထပ်ကာ ကြားရပြီး အတုဆန်သည်。

⚠️ tag တိုင်းကို **တိုင်းယူသည်** — ဖိုင်နာမည်ကနေ မှန်းဆတာ မဟုတ်ပါ。
   (နာမည်က role အကြံပြုချက်သာ · `role_src` မှာ မှတ်ထားသည်)
"""
import json
import os
import re
import sys
import wave

import numpy as np

# ⚠️ နာမည်ကနေ role ခန့်မှန်း — **အတည်ပြုချက် မဟုတ်**
HINT = [
    (r"whoosh|swoosh|sweep|swish", "whoosh"),
    (r"impact|hit|boom|slam|thud", "impact"),
    (r"click|mouse|tick|tap", "click"),
    (r"pop|blip|bubble", "pop"),
    (r"riser|rise|build|swell", "riser"),
    (r"latch|lock|snap|clasp", "latch"),
    (r"swipe|slide|drag", "swipe"),
    (r"key|type|keyboard", "type"),
    (r"shimmer|sparkle|chime|bell|glimmer", "shimmer"),
    (r"glitch|digital|error", "glitch"),
    (r"sub|drop|deep|low", "sub"),
    (r"air|texture|amb|room|noise", "air"),
    (r"shutter|camera", "shutter"),
    (r"success|correct|win|positive", "success"),
    (r"wrong|fail|negative|denied", "error"),
]


def role_of(name):
    n = name.lower()
    for pat, r in HINT:
        if re.search(pat, n):
            return r
    return "unknown"


def read_wav(path, max_s=12.0):
    """RIFF ကို **ကိုယ်တိုင် ဖတ်**သည် → `(samples, sr, ch, sw, nframes)`

    ⚠️ Python ရဲ့ `wave` က **WAVE_FORMAT_EXTENSIBLE (0xFFFE)** ကို ငြင်းသည် —
       「unknown format: 65534」。 motionkit ရဲ့ ၄၉၇ ဖိုင်လုံး အဲဒီပုံစံ
       ဖြစ်နေသဖြင့် `wave` နဲ့ **တစ်ဖိုင်မှ မဖတ်နိုင်**ပါ (၂၀၂၆-၀၉-၂၁)。
    ⚠️ ffmpeg နဲ့ ဖတ်လျှင် subprocess ၄၉၇ ခါ — အလွန်ကြာသည် ⇒ ကိုယ်တိုင် ဖတ်。
    """
    import struct
    with open(path, "rb") as f:
        if f.read(4) != b"RIFF":
            return None
        f.read(4)
        if f.read(4) != b"WAVE":
            return None
        fmt = None
        while True:
            h = f.read(8)
            if len(h) < 8:
                return None
            cid, sz = struct.unpack("<4sI", h)
            if cid == b"fmt ":
                d = f.read(sz)
                tag, ch, sr, _br, _ba, bits = struct.unpack("<HHIIHH", d[:16])
                if tag == 0xFFFE and len(d) >= 40:
                    tag = struct.unpack("<H", d[24:26])[0]
                fmt = (tag, ch, sr, bits)
            elif cid == b"data":
                if not fmt:
                    return None
                tag, ch, sr, bits = fmt
                sw = bits // 8
                want = min(sz, int(sr * ch * sw * max_s))
                raw = f.read(want)
                n = sz // max(1, ch * sw)
                return raw, sr, ch, sw, n, tag
            else:
                f.seek(sz + (sz & 1), 1)


def measure(path):
    """wav တစ်ဖိုင် — တိုင်းချက် dict · မရလျှင် None"""
    r = read_wav(path)
    if not r:
        return None
    raw, sr, ch, sw, n, tag = r
    if n <= 0 or sw not in (2, 3, 4) or tag not in (1, 3):
        return None
    if tag == 3 and sw == 4:                      # IEEE float32
        a = np.frombuffer(raw[:len(raw) // 4 * 4], "<f4").astype(np.float32)
    elif sw == 2:
        a = np.frombuffer(raw[:len(raw) // 2 * 2], "<i2").astype(np.float32) / 32768.0
    elif sw == 4:
        a = np.frombuffer(raw[:len(raw) // 4 * 4], "<i4").astype(np.float32) / 2147483648.0
    else:
        b = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.int32)
        a = ((b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
              | -((b[:, 2] & 0x80) << 17)).astype(np.float32) / 8388608.0)
    if not len(a):
        return None
    if ch > 1:
        a = a[:len(a) // ch * ch].reshape(-1, ch)
        L, R = a[:, 0], a[:, 1] if ch > 1 else a[:, 0]
        # ⚠️ width — L/R ကွာဟမှု。 mono ဆိုလျှင် ၀
        width = float(np.abs(L - R).mean() / max(1e-6, np.abs(L + R).mean() / 2))
        m = a.mean(1)
    else:
        width = 0.0
        m = a
    dur = n / float(sr)
    # ⚠️ peak ကို **channel တစ်ခုချင်း** ကနေ ယူရမည် — `m` (mono ပေါင်းချက်)
    #    ကနေ ယူလျှင် Haas stereo ဖိုင်များမှာ ၁.၃ dB အထိ **နိမ့်**သွားသည်
    #    (cine_2026/whoosh_fast_03 — ကိုယ်တိုင် -2.8 · ffmpeg -1.5 · ၂၀၂၆-၀၉-၂၁)。
    #    ⇒ အဲဒီ peak နဲ့ normalise လျှင် ကျယ်သော channel က ကျော်လွန်ပြီး
    #      limiter ကို အားကိုးရသည် ⇒ 「peak ပြန့်ကျဲ」 ဖြစ်ရာ。
    peak = float(np.abs(a).max())
    peak_mid = float(np.abs(m).max())
    # ⚠️ **အကျယ်ဆုံး ၃၀၀ ms ဗိန်ဒိုး ရဲ RMS** — အသံ အားကို တိုင်းရန်。
    #    peak နဲ့ normalise လျှင် variant တွေ ၁၂ dB ကွာနေသည် (တိုင်းပြီး
    #    တွေ့ · ၂၀၂၆-၀၉-၂၁) — transient တစ်ချက်က peak တူပေမယ့် အား နည်းသည်。
    #    ⚠️ ဖိုင်တစ်ခုလုံးရဲ RMS ကို မသုံးရ — click မှာ အစောက်ပိုင်းက
    #    များသဖြင့် RMS ကျပြီး အလွန် ကြယ်သွားမည်。 ငှော့ ဗိန်ဒိုးက LUFS-S နဲ့ နီးသည်。
    _w = max(1, int(sr * 0.3))
    if len(m) <= _w:
        loud = float(np.sqrt((m.astype(np.float64) ** 2).mean()))
        peak_t = float(int(np.argmax(np.abs(m))) / sr)
    else:
        _c = np.cumsum(np.concatenate(([0.0], m.astype(np.float64) ** 2)))
        _e = (_c[_w:] - _c[:-_w]) / _w
        loud = float(np.sqrt(_e.max()))
        # ⚠️ **အသံ က ဘယ်အချိန်မှာ ဆိုက်မိတ်လဲ**。 riser က နောက်ဆုံးမှ ကျယ်သည် —
        #    ဂရပ်ဖစ် လာချိန်က cue အစား ထည့်လျှင် ၁.၇s နောက်ကျမှ ကျယ်သည်
        #    (တကန် တိုင်းတွေ့ · ၂၀၂၆-၀၉-၂၁)。 ⇒ အသံ ကျယ်ချိန်ကို မှတ်ထားသည် —
        #    `sfxpool.lead()` က ဒီကို သုံးပြီး **အချိန်ကိုက်အောင် အစား ထည့်**သည်。
        peak_t = float((int(np.argmax(_e)) + _w / 2.0) / sr)
    rms = float(np.sqrt((m ** 2).mean()))
    # ⚠️ brightness — spectral centroid (Hz)。 「တောက်」「မှိန်」ခွဲရန်
    k = min(len(m), 1 << 15)
    F = np.abs(np.fft.rfft(m[:k] * np.hanning(k)))
    f = np.fft.rfftfreq(k, 1.0 / sr)
    cen = float((F * f).sum() / max(1e-9, F.sum()))
    # ⚠️ impact — အစ ၅၀ms ရဲ့ စွမ်းအင် ÷ စုစုပေါင်း。 「ထိုးကွင်း」ခွဲရန်
    h = max(1, int(sr * 0.05))
    imp = float((m[:h] ** 2).sum() / max(1e-12, (m ** 2).sum()))
    return dict(dur=round(dur, 3), sr=sr, ch=ch,
                peak_db=round(20 * np.log10(max(1e-6, peak)), 1),
                peak_mid_db=round(20 * np.log10(max(1e-6, peak_mid)), 1),
                loud_db=round(20 * np.log10(max(1e-6, loud)), 1),
                peak_t=round(peak_t, 3),
                rms_db=round(20 * np.log10(max(1e-6, rms)), 1),
                brightness=int(cen), width=round(min(2.0, width), 3),
                impact=round(imp, 3))

# ⚠️ **လိုင်စင် မျဉ်း — ဒါက စီးပွားရေး ကိစ္စ、အသံ ကိစ္စ မဟုတ်။**
#    youtubesfx / Mixkit တို့က 「ဗီဒီယိုထဲ သုံးခွင့်」ပေးသည် —
#    **ဖိုင်ကို product ထဲ ထည့်ဖြန့်ခြင်း ကို တားသည်**。 IKKI က SaaS ဖြစ်၍
#    render ထွက်တာ **customer ရဲ့ ဗီဒီယို** — Zin ရဲ့ မဟုတ် ⇒ ထို pack ကို
#    ပုံသေအနေနဲ့ **မသုံးပါ**。 ကိုယ်ပိုင် synthesis နဲ့ CC0 သာ ship လုပ်သည်。
BANK = {
    # legacy root — <root>/assets/sfx
    "cue":        ("youtubesfx-pack", False, "ဗီဒီယိုထဲသာ · product ထဲ ဖြန့်ခွင့် မရ"),
    "zjl":        ("youtubesfx-pack", False, "cue ရဲ့ highpass ဗားရှင်း — လိုင်စင် တူ"),
    "youtubesfx": ("youtubesfx-pack", False, "မူရင်း ဒေါင်းထား"),
    "gen":        ("own-synthesis",   True,  "sfxgen.py — ကိုယ်တိုင် ဆောက်"),
    "premium":    ("own-synthesis",   True,  "ကိုယ်တိုင် ဆောက်"),
    # motionkit root — <mk>/assets/sfx
    "gen2026":         ("own-synthesis", True, "sfx2026.py — ကိုယ်တိုင် ဆောက်"),
    "gen2026_creator": ("own-synthesis", True, "sfx2026.py creator profile"),
    "hybrid_2026":     ("own-synthesis", True, "hybrid26.py — gen + cc0 ရွေးချယ်"),
    "cine_2026":       ("own-synthesis", True, "ကိုယ်တိုင် ဆောက်"),
    "cc0_2026":        ("cc0",          True, "Openverse/Freesound CC0 — အသံသွင်းချက်"),
}
# ⚠️ ဤဖိုလ်ဒါများက **ထုတ်ယူပြီးသား cache** — မူရင်း မဟုတ် ⇒ မထည့်ရ
SKIP = {"role", "role_gen", "bed"}


def build(roots, out):
    """catalog v2 — root အများအပြား · လိုင်စင် အမှတ်အသား ပါ"""
    items, rmap = [], {}
    for rid, root in roots:
        rmap[rid] = root
        for dp, _dn, fn in os.walk(root):
            bank = os.path.relpath(dp, root).split(os.sep)[0]
            if bank in SKIP or bank == ".":
                continue
            for f in sorted(fn):
                if not f.lower().endswith(".wav"):
                    continue
                p = os.path.join(dp, f)
                m = measure(p)
                if not m:
                    continue
                lic, ship, note = BANK.get(bank, ("unknown", False, "မသိ"))
                m.update(id=f"{bank}/{os.path.splitext(f)[0]}", bank=bank,
                         root=rid, path=os.path.relpath(p, root),
                         role=role_of(f), role_src="filename",
                         license=lic, ship=ship, lic_note=note)
                items.append(m)
    doc = dict(version=2, roots=rmap,
               _doc="⚠️ `role` က **ဖိုင်နာမည်ကနေ ခန့်မှန်း**ထားသည် "
                    "(`role_src: filename`) — နားထောင်ပြီး အတည်ပြုရသေး。 "
                    "ကျန် tag အားလုံးကို sample ကနေ တိုင်းယူထားသည်。 "
                    "⚠️ `ship: false` = ရောင်းသော product ထဲ **မသုံးရ** "
                    "(youtubesfx pack က ဖိုင် ဖြန့်ခွင့် မပေး)。",
               n=len(items), items=items)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False)
    return doc


if __name__ == "__main__":
    out = sys.argv[1]
    rs = [tuple(a.split("=", 1)) for a in sys.argv[2:]]
    d = build(rs, out)
    import collections
    print(f"catalog v{d['version']} · {d['n']} ဖိုင်")
    c = collections.Counter((x["license"], x["ship"]) for x in d["items"])
    for (lic, sh), n in sorted(c.items()):
        print(f"  {lic:16} ship={str(sh):5} {n:4}")
