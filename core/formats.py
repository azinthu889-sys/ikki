#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · ထုတ်လုပ်မည့် အရွယ် (format) — brand နှင့် **ခွဲထားသည်**。

⚠️ အရင်က အရွယ်ကို brand ထဲ ကပ်ထားခဲ့သည် (zae=1080×1440 · zjl=1920×1080)。
   ဒါဆိုလျှင် "ZAE style နဲ့ TikTok 9:16 လိုချင်တယ်" ဆိုတာ လုပ်လို့ မရဘူး —
   brand က identity (အရောင် · ဖောင့်)、format က delivery (အရွယ် · safe zone)。
   ⇒ ဒီနှစ်ခုကို ခွဲပြီး video တစ်ခုချင်း ရွေးလို့ရအောင် လုပ်သည်。

**safe zone ဆိုတာ ဘာလဲ** — TOP..BOT ဟာ ဂရပ်ဖစ် ချလို့ရသော အလျားလိုက် အပိုင်း。
  - အပေါ်ဘက် — platform ရဲ့ UI (tab · search) ဖုံးသော အပိုင်း ချန်ရသည်
  - အောက်ဘက် — ① platform UI (caption · music ticker) ② IKKI ရဲ့ စာတန်းဘန်း

⚠️ **တိုင်းထားသော ကိန်း** နှင့် **အချိုးဖြင့် တွက်ထားသော ကိန်း** ကို ခွဲ မှတ်ထားသည်。
   measured=True ဖြစ်သော format တွေကို **မပြောင်းရ** — reference ဗီဒီယိုမှ
   တိုင်းယူထားသည်。
"""

FORMATS = {
 # ── ဒေါင်လိုက် ─────────────────────────────────────────
 "9:16": dict(
    W=1080, H=1920, label="TikTok · Reels · Shorts", group="vertical",
    # ⚠️ TikTok ရဲ့ app UI က ဗီဒီယိုပေါ် ဖုံးသည် — တိုင်းထားသည်:
    #    အောက် ၃၂၀px (username · caption · music · progress)
    #    အပေါ် ၁၃၀px (Following/For You · search) · ညာ ၁၄၀px (avatar · like)
    TOP=130, BOT=1600, SIDE_R=140, SIDE_L=60, measured=True,
 ),
 "3:4": dict(
    W=1080, H=1440, label="ZAE short-form", group="vertical",
    # ⚠️ READING TIPS ရဲ့ စာတမ်းက y 969 မှ 1238 — BOT 940 က ၂၉px ချန်သည်
    TOP=300, BOT=940, SIDE_R=60, SIDE_L=60, measured=True,
 ),
 "4:5": dict(
    W=1080, H=1350, label="Instagram feed", group="vertical",
    # အချိုးဖြင့် တွက် — 3:4 ရဲ့ အချိုး (TOP .208 · BOT .653) ကို သုံးသည်
    TOP=281, BOT=882, SIDE_R=60, SIDE_L=60, measured=False,
 ),
 # ── စတုရန်း ───────────────────────────────────────────
 "1:1": dict(
    W=1080, H=1080, label="Feed · LinkedIn", group="square",
    TOP=225, BOT=705, SIDE_R=60, SIDE_L=60, measured=False,
 ),
 # ── အလျားလိုက် ─────────────────────────────────────────
 "16:9": dict(
    W=1920, H=1080, label="YouTube · Podcast", group="horizontal",
    # ⚠️ ZJL house style မှ — စာတမ်း y≈892
    TOP=170, BOT=830, SIDE_R=60, SIDE_L=60, measured=True,
 ),
 # ⚠️ 4K က 16:9 ရဲ **အချိုး တူညီစွာ** (၁၆:၉) — အရွယ်သာ ၂ ဆ ဖြစ်သည်。
 #    safe zone ဆိုတာက **ဘောင်ရဲ့ အချိုး** ဖြစ်၍ ၁၆:၉ မှာ တိုင်းထားသည်ကို
 #    တိတိကျကျ ၂ ဆ တွက်လျှင် ရသည် — မှန်းဆချက် မဟုတ်。
 #    ⇒ `measured=True`。 (အရင်က False ဖြစ်၍ render log မှာ
 #      「အချိုးတွက်」 ဟု သတိပေးနေခဲ့သည် — မဟုတ်မှန်ကန် သတိပေးချက်)。
 "4K16:9": dict(
    W=3840, H=2160, label="YouTube 4K", group="horizontal",
    TOP=340, BOT=1660, SIDE_R=120, SIDE_L=120, measured=True,
 ),
}

# brand တစ်ခုချင်းရဲ့ မူလ format — မရွေးလျှင် ဒါကို သုံးသည်
NATIVE = {"zae": "3:4", "zjl": "16:9"}

def get(key, brand=None):
    if key in FORMATS: return dict(FORMATS[key], key=key)
    k = NATIVE.get(brand or "", "16:9")
    return dict(FORMATS[k], key=k)

def keys():   return list(FORMATS)

def listing():
    """UI အတွက် — group အလိုက် စီထားသည်"""
    out = []
    for g in ("vertical", "square", "horizontal"):
        for k, v in FORMATS.items():
            if v["group"] == g:
                out.append(dict(key=k, label=v["label"], w=v["W"], h=v["H"],
                                group=g, measured=v["measured"]))
    return out

def theme(brand, fmt):
    """brand (အရောင်/ဖောင့်) + format (အရွယ်/safe zone) → motionkit theme dict。

    ⚠️ brand ရဲ့ native format ဖြစ်လျှင် **တိုင်းထားသော TOP/BOT ကို အတိအကျ**
       သုံးရမည် — အချိုးနဲ့ ပြန်တွက်လျှင် reference နှင့် လွဲသွားမည်。
    """
    f = get(fmt, brand.get("id"))
    c = brand.get("colors") or []
    def col(i, d): return c[i] if i < len(c) and c[i] else d
    return dict(
        W=f["W"], H=f["H"],
        NAVY=col(0, "#0B1B33"), DEEP=col(1, "#16304C"),
        BLUE=col(3, "#2E86C1"), SKY=col(3, "#4FA8DC"),
        GOLD=col(2, "#F5C543"), AMBER=col(2, "#FBBF4A"),
        WHITE="#FFFFFF", RED=col(4, "#E5484D"),
        PANEL=col(1, "#16304C"), PANEL_A=0.93, BG=col(0, "#0B1B33"),
        MMF=brand.get("mmf") or "Pyidaungsu-Bold",
        LATIN=brand.get("latin") or "Figtree-Black",
        LT=brand.get("latin") or "Figtree-Black",
        JP=brand.get("jp") or "HiraginoSans-W7",
        TOP=f["TOP"], BOT=f["BOT"],
        SUB_STROKE=col(0, "#1E3B5A"),
        _fmt=f["key"],
    )
