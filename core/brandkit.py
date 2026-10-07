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

# ⚠️ ၂၀၂၆-၁၀-၀၇ 「user ၁၀၀၀ အတွက် ၅ မျိုး မလောက်」 ⇒ ၂၄ မျိုး (variant ၇ × radius × ဂဏန်း font × motion)。
#    ကျပန်း ပေါင်းစပ်မှု မဟုတ် — ကြည့်ကောင်းအောင် **ရွေးထားသော** စုံတွဲများ (dark/light တစ်ဝက်စီ ခန့်)。
#    ⚠️ pack = hash(brand id) % len(PACKS) ⇒ **အရေအတွက် ပြောင်းလျှင် user အားလုံးရဲ့ pack ပြောင်း**。
#       ၅ ⇒ ၂၄ ကို beats launch မတိုင်ခင် (user မမြင်ရသေး) တစ်ကြိမ် ပြောင်းခဲ့သည်။ launch ပြီးနောက်
#       ထပ်တိုးလိုလျှင် account အလိုက် ရွေးပြီးသား pack ကို DB မှာ သိမ်းပြီးမှ တိုးရမည် (`beat_pack_name`)。
def _pk(name, variant, radius, num="Anton", motion="snappy"):
    return dict(name=name, variant=variant, radius=radius, num=num, motion=motion)


PACKS = (
    _pk("glass-28", "glass", 28),
    _pk("glass-40", "glass", 40),
    _pk("light-24", "light", 24),
    _pk("neon-20", "neon", 20),
    _pk("glass-16", "glass", 16),
    # ── ၂၀၂၆-၁၀-၀၇ ထပ်တိုး ──
    _pk("solid-pop", "solid", 32, "Anton", "bouncy"),
    _pk("solid-clean", "solid", 18, "InterV", "smooth"),
    _pk("outline-edge", "outline", 10, "InterV", "snappy"),
    _pk("outline-soft", "outline", 36, "Anton", "smooth"),
    _pk("paper-editorial", "paper", 14, "InterV", "smooth"),
    _pk("paper-round", "paper", 34, "Anton", "bouncy"),
    _pk("frost-air", "frost", 30, "InterV", "smooth"),
    _pk("frost-bold", "frost", 22, "Anton", "snappy"),
    _pk("glass-smooth", "glass", 24, "InterV", "smooth"),
    _pk("glass-bouncy", "glass", 44, "Anton", "bouncy"),
    _pk("light-ios", "light", 30, "InterV", "snappy"),
    _pk("light-bouncy", "light", 40, "Anton", "bouncy"),
    _pk("neon-sharp", "neon", 8, "InterV", "snappy"),
    _pk("neon-round", "neon", 32, "Anton", "smooth"),
    _pk("solid-square", "solid", 6, "Anton", "snappy"),
    _pk("outline-pill", "outline", 48, "InterV", "bouncy"),
    _pk("paper-sharp", "paper", 6, "Anton", "snappy"),
    _pk("frost-round", "frost", 44, "Anton", "bouncy"),
    _pk("glass-sharp", "glass", 8, "InterV", "snappy"),
)
VARIANTS = ("glass", "light", "neon", "solid", "outline", "paper", "frost")

DEFAULT_ACCENT = "#FFD60A"
HOUSE = ("ikki", "zae", "zjl")


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
    # ⚠️ ဦးစားပေး (၂၀၂၆-၁၀-၀၇): user ကိုယ်ပိုင် brand အရောင် > reference accent > style (recipe) accent
    #    (house brand ikki/zae/zjl ဆိုလျှင် brand အရောင် မဟုတ် ⇒ reference/style ကို ယူ)
    own = bool(bd.get("colors")) and str(bd.get("id") or "") not in HOUSE
    if not own and rc.get("ref_accent"):
        acc, acc2 = accent_pair([rc["ref_accent"]])
    elif not own and rc.get("accent"):
        acc, acc2 = accent_pair([rc["accent"]])
    pk = pack_for(seed or bd.get("id"))
    if rc.get("beat_pack_name"):
        pk = next((p for p in PACKS if p["name"] == rc["beat_pack_name"]), pk)
    out = dict(accent=acc, accent2=acc2, ink=ink_for(acc),
               variant=rc.get("beat_variant") or pk["variant"],
               radius=int(rc.get("beat_radius") or pk["radius"]),
               num=pk.get("num", "Anton"), motion=pk.get("motion", "snappy"), pack=pk["name"])
    return out
