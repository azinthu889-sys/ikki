#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Brand kit ⇒ Remotion beat kit theme (Zin ၂၀၂၆-၁၀-၀၇ roadmap ③)

「user တိုင်း ထုတ်တဲ့ ဗီဒီယို ပုံစံ တစ်မျိုးတည်း ထွက်မလား」 ⇒ **မထွက်ရ**。
  · user brand ရဲ့ `colors` ထဲက အတောက်ဆုံး/အရောင်အရှိဆုံး ⇒ accent · ပိုမှောင် ⇒ accent2
  · style pack (variant glass/light/neon · radius) ကို brand id နဲ့ **တည်ငြိမ်စွာ** ရွေး
    (user တစ်ယောက် ⇒ ဗီဒီယိုတိုင်း တစ်ပုံစံတည်း = brand consistency · user ကွဲ ⇒ ပုံစံကွဲ)
  · recipe (`accent` · `beat_variant` · `beat_radius`) က လွှမ်းနိုင်
"""
import colorsys
import hashlib

PACKS = (
    dict(name="glass-28", variant="glass", radius=28),
    dict(name="glass-40", variant="glass", radius=40),
    dict(name="light-24", variant="light", radius=24),
    dict(name="neon-20", variant="neon", radius=20),
    dict(name="glass-16", variant="glass", radius=16),
)
DEFAULT_ACCENT = "#FFD60A"


def _rgb(h):
    h = str(h or "").strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return None
    try:
        return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        return None


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, int(round(c * 255)))):02X}" for c in rgb)


def _score(rgb):
    hh, ll, ss = colorsys.rgb_to_hls(*rgb)
    # ⚠️ မှောင်လွန်း/ဖြူလွန်း ⇒ dark glass ပေါ်မှာ accent မဖြစ်နိုင်
    if ll < 0.25 or ll > 0.9:
        return -1
    return ss * (1 - abs(ll - 0.55))


def accent_pair(colors):
    best = None
    for c in colors or []:
        rgb = _rgb(c)
        if rgb is None:
            continue
        s = _score(rgb)
        if s > 0.15 and (best is None or s > best[0]):
            best = (s, rgb)
    rgb = best[1] if best else _rgb(DEFAULT_ACCENT)
    hh, ll, ss = colorsys.rgb_to_hls(*rgb)
    a2 = colorsys.hls_to_rgb((hh - 0.03) % 1.0, max(0.25, ll - 0.14), min(1.0, ss * 1.05))
    return _hex(rgb), _hex(a2)


def ink_for(accent):
    r, g, b = _rgb(accent) or (1, 1, 1)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#0B0B0C" if lum > 0.5 else "#FFFFFF"


def pack_for(seed):
    h = int(hashlib.sha1(str(seed or "ikki").encode()).hexdigest()[:8], 16)
    return PACKS[h % len(PACKS)]


def kit(bd=None, rc=None, seed=None):
    """`bd` (run.py ရဲ့ brand dict — colors · mmf · latin) + recipe ⇒ Remotion `Brand`"""
    bd, rc = bd or {}, rc or {}
    acc, acc2 = accent_pair(bd.get("colors"))
    if rc.get("accent"):
        acc, acc2 = accent_pair([rc["accent"]])
    pk = pack_for(seed or bd.get("id"))
    out = dict(accent=acc, accent2=acc2, ink=ink_for(acc),
               variant=rc.get("beat_variant") or pk["variant"],
               radius=int(rc.get("beat_radius") or pk["radius"]), pack=pk["name"])
    return out
