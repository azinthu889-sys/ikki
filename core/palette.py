#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · logo → brand အရောင် ၅ ခု。

သုံးစွဲသူက logo တင်လိုက်တာနဲ့ ထွက်လာမယ့် ဗီဒီယိုက **သူ့ theme အတိုင်း**
ဖြစ်ရမည် ⇒ logo ထဲက အရောင်ကို ထုတ်ပြီး `brand.colors` ထဲ ထည့်ပေးသည်。

⚠️ `formats.theme()` က အရောင် ၅ ခုကို ဤအစီအစဉ်အတိုင်း သုံးသည် —
      [0] BG · NAVY · SUB_STROKE      ← **မှောင်ရမည်**
      [1] PANEL · DEEP                ← [0] ထက် အနည်းငယ် လင်း
      [2] GOLD · AMBER  (အဓိက accent) ← logo ရဲ့ အရောင်အစစ်
      [3] BLUE · SKY    (ဒုတိယ)
      [4] RED           (သတိပေး)

⚠️ **[0] ကို logo ရဲ့ အရောင်အတိုင်း တိုက်ရိုက် မထားရ**。 logo က အဝါ ဒါမှမဟုတ်
   အဖြူဆိုလျှင် နောက်ခံက လင်းပြီး အဖြူစာတန်း လုံးဝ မမြင်ရတော့ဘူး。
   ⇒ logo ရဲ့ **အဆင်း (hue)** ကို ယူပြီး အလင်းကို အတင်း ချသည်。
"""
import colorsys


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def _hsv(rgb):
    return colorsys.rgb_to_hsv(*[c / 255.0 for c in rgb])


def _rgb(h, s, v):
    return tuple(c * 255.0 for c in colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v))))


def _lum(rgb):
    return (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000.0


def extract(path, n=10):
    """logo ဖိုင် → (colors[5], info)。 PIL မရလျှင် ValueError。"""
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    im.thumbnail((220, 220))
    px = list(im.getdata())
    # ⚠️ ဖောက်ထားသော pixel ကို ဖယ်ရမည် — မဖယ်လျှင် အနက်/အဖြူ နောက်ခံက
    #    အရောင်တွေကို လွှမ်းပြီး logo ရဲ့ အရောင်အစစ် ပျောက်သည်。
    solid = [(r, g, b) for r, g, b, a in px if a > 160]
    if not solid:
        raise ValueError("logo မှာ မှုန်မဝင် pixel မရှိ")
    # အရောင် ရှိသော pixel (အဖြူ/အနက်/မီးခိုး မဟုတ်) ကို သီးသန့် ရေတွက်
    buckets = {}
    for r, g, b in solid:
        h, s, v = _hsv((r, g, b))
        if s < 0.18 or v < 0.12 or v > 0.97:
            continue
        k = (int(h * 18) % 18, int(s * 3), int(v * 3))
        e = buckets.setdefault(k, [0, 0, 0, 0])
        e[0] += r; e[1] += g; e[2] += b; e[3] += 1
    ranked = sorted(buckets.values(), key=lambda e: -e[3])
    hues = [(e[0] / e[3], e[1] / e[3], e[2] / e[3], e[3]) for e in ranked[:n]]

    if hues:
        acc = hues[0][:3]
        ah, as_, av = _hsv(acc)
        # accent ကို ဖတ်ရလွယ်အောင် အနည်းငယ် တောက်စေသည်
        acc = _rgb(ah, max(as_, 0.55), max(av, 0.62))
        # ဒုတိယ အဆင်း — accent နဲ့ ကွာသော hue ရှိမှ၊ မရှိလျှင် accent ရဲ့ အေးဘက်
        sec = None
        for r, g, b, _c in hues[1:]:
            h2 = _hsv((r, g, b))[0]
            if min(abs(h2 - ah), 1 - abs(h2 - ah)) > 0.08:
                sec = _rgb(h2, 0.55, 0.72); break
        if sec is None:
            sec = _rgb(ah + 0.5, 0.45, 0.75)
        note = "logo ရဲ့ အရောင်အဓိကမှ"
    else:
        # ⚠️ အဖြူ/အနက် logo — အဆင်း မရှိ。 မှန်းမရေးရ ⇒ house ပုံသေ。
        acc = (245, 197, 67); sec = (79, 168, 220)
        ah = _hsv(acc)[0]
        note = "logo မှာ အရောင် မပါ (အဖြူ/အနက်) — house ပုံသေ သုံးသည်"

    # နောက်ခံ — accent ရဲ့ အဆင်းကို ယူပြီး **အလင်း အတင်း ချ**
    bg = _rgb(ah, 0.55, 0.13)
    panel = _rgb(ah, 0.45, 0.24)
    red = (229, 72, 77)
    cols = [_hex(bg), _hex(panel), _hex(acc), _hex(sec), _hex(red)]
    info = dict(note=note, accent_lum=round(_lum(acc), 1), bg_lum=round(_lum(bg), 1),
                colored_px=sum(e[3] for e in ranked), solid_px=len(solid))
    return cols, info


if __name__ == "__main__":
    import sys
    c, i = extract(sys.argv[1])
    print("  ", " ".join(c))
    print("  ", i)
