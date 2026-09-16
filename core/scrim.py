#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · အပေါ်ပိုင်း navy scrim。

⚠️ ZAE က **အဖြူ studio wall** ပေါ် ရိုက်သည် (RGB ≈ 245,242,243)。
   အဖြူစာလုံးက အဖြူနောက်ခံပေါ် **လုံးဝ မမြင်ရ** — တကယ် ဖြစ်ခဲ့သည်。
   ⇒ ဂရပ်ဖစ် အောက်မှာ navy gradient scrim ခံရသည် (broadcast ရဲ့ ပုံမှန်နည်း)。

⚠️ scrim ရဲ့ အမြင့်နှင့် အလင်းပိတ်မှုကို **တိုင်းထားသည်** — 460px (frame
   1440 အတွက်)。 အချိုးဖြင့် ပြန်တွက်သည်。

⚠️ ALPHA ၀.၆၂ က **မှားမနေ** — မှားခဲ့တာ *တစ်လျှောက်လုံး ဖွင့်ထားတာ*。
   N5 ရဲ့ ပြောသူ frame တွေကို တစ်ချပ်ချင်း တိုင်းတော့ အပေါ်၃၃% အလင်းက
     ဂရပ်ဖစ် မရှိချိန် **၂၃၆** ↔ ရှိချိန် **၁၄၉**
   ဟု ပြောင်းနေသည်。 IKKI က ၁၈၇ မှာ ငြိမ်နေခဲ့သည်。 α၀.၃၅ ဖြင့် ၂၃၆→၁၈၇
   ကျသဖြင့် ၁၄၉ အတွက် **၀.၆၂** ပင် လိုသည် ⇒ α ပြန်တင်ပြီး `track()` ဖြင့်
   ဂရပ်ဖစ်ပေါ်မှာသာ ပြသည်。
   ⚠️ အစောပိုင်းက "α ၂ ဆ ပြင်းနေသည်" ဟု ငါ ကောက်ချက်ချခဲ့သည်မှာ **မှား** —
      B-roll frame တွေ ရောထားသော ပျမ်းမျှနှင့် တိုက်မိ၍。
"""
import os, subprocess

FRAC_H = 460/1440.0   # frame အမြင့်၏ ~32%
ALPHA  = 0.62

def png(work, W, H, navy, frac=FRAC_H, alpha=ALPHA):
    h = int(H*frac)
    p = os.path.join(work, "_scrim.png")
    if os.path.exists(p): return p, h
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}">'
           f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0%" stop-color="{navy}" stop-opacity="{alpha}"/>'
           f'<stop offset="62%" stop-color="{navy}" stop-opacity="{alpha*0.55:.3f}"/>'
           f'<stop offset="100%" stop-color="{navy}" stop-opacity="0"/>'
           f'</linearGradient></defs>'
           f'<rect width="{W}" height="{h}" fill="url(#g)"/></svg>')
    # ⚠️ rsvg-convert ကိုသာ သုံးရသည် — resvg နှင့် ffmpeg drawtext က မရ
    subprocess.run(["rsvg-convert","-w",str(W),"-h",str(h),"-o",p],
                   input=svg.encode(), check=True)
    return p, h


def _band(W, H, navy, a, y0, y1, out, soft=100, maxfrac=0.34):
    """y0..y1 ကို ဖုံးသော gradient band — အနားနှစ်ဖက် ပျောက်သွားသည်。

    ⚠️ band ကို **ကန့်သတ်ရမည်** — ဂရပ်ဖစ်ရဲ့ bbox က ကျယ်နေလျှင်
       ဖန်သားပြင် တစ်ဝက် မှောင်သွားသည် (v36 မှာ တကယ် ဖြစ်ခဲ့)。
    """
    if y1 - y0 > H*maxfrac:                      # အလယ်ဗဟိုမှ ဖြတ်
        c = (y0+y1)//2; h2 = int(H*maxfrac)//2
        y0, y1 = c-h2, c+h2
    top = max(0, y0 - soft); bot = min(H, y1 + soft)
    if bot <= top: top, bot = 0, min(H, int(H*0.32))
    h = bot - top
    f1 = max(0.02, min(0.45, soft/float(h)))
    f2 = 1.0 - f1
    if a <= 0:
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"/>'
    else:
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">'
               f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
               f'<stop offset="0%" stop-color="{navy}" stop-opacity="0"/>'
               f'<stop offset="{f1*100:.1f}%" stop-color="{navy}" stop-opacity="{a:.3f}"/>'
               f'<stop offset="{f2*100:.1f}%" stop-color="{navy}" stop-opacity="{a:.3f}"/>'
               f'<stop offset="100%" stop-color="{navy}" stop-opacity="0"/>'
               f'</linearGradient></defs>'
               f'<rect x="0" y="{top}" width="{W}" height="{h}" fill="url(#g)"/></svg>')
    subprocess.run(["rsvg-convert","-w",str(W),"-h",str(H),"-o",out],
                   input=svg.encode(), check=True)
    return out


def track(wins, out, work, W, H, navy, fps=30, total=0.0,
          frac=FRAC_H, alpha=ALPHA, fade=0.30):
    """ဂရပ်ဖစ် ပေါ်နေချိန်မှာသာ ပေါ်သော scrim track (alpha .mov တစ်ခု)。

    ⚠️ scrim ကို **ဗီဒီယိုတစ်ခုလုံး** ခံထားလျှင် ပြောသူ shot တွေပါ
       မှောင်သွားသည်。 N5 reference ကို ပြောသူ frame အလိုက် တိုင်းတော့
       အပေါ်၃၃% အလင်းက **၁၄၉ ↔ ၂၃၆ ကြား ပြောင်းနေ**သည် — ဂရပ်ဖစ်
       ရှိချိန်မှာ မှောင်ပြီး မရှိချိန်မှာ မူရင်းအတိုင်း。 IKKI ကတော့
       ၁၈၇ မှာ တစ်လျှောက်လုံး ငြိမ်နေခဲ့သည် (တကယ် ဖြစ်ခဲ့)。
    ⚠️ ရုတ်တရက် ပေါ်/ပျောက်လျှင် မျက်စိထဲ ခုန်သည် ⇒ ထစ် ၅ ဆင့်ဖြင့်
       fade ဝင်/ထွက် လုပ်သည် (စာတန်း track နည်းအတိုင်း concat)。
    """
    if not wins: return None
    os.makedirs(work, exist_ok=True)
    STEPS = 5
    blank = os.path.join(work, "_sc_blank.png")
    if not os.path.exists(blank):
        _band(W, H, navy, 0.0, 0, 0, blank)
    items=[]; t=0.0
    st = fade/STEPS
    for wi, w in enumerate(sorted(wins)):
        a, b = w[0], w[1]
        # ⚠️ band ကို ဂရပ်ဖစ်ရဲ့ တကယ့် အမြင့်အတိုင်း — ပုံသေ အပေါ်ပိုင်း မဟုတ်
        y0 = w[2] if len(w) > 2 else 0
        y1 = w[3] if len(w) > 3 else int(H*frac)
        lvl = {}
        for k in range(STEPS+1):
            q = os.path.join(work, f"_sc{wi}_{k}.png")
            if not os.path.exists(q):
                _band(W, H, navy, alpha*k/STEPS, y0, y1, q)
            lvl[k] = q
        a = max(0.0, a - fade); b = max(a+0.1, b)
        if a > t + 0.02: items.append((blank, a-t))
        for k in range(1, STEPS+1): items.append((lvl[k], st))
        hold = (b - a) - 2*fade
        if hold > 0.02: items.append((lvl[STEPS], hold))
        for k in range(STEPS-1, -1, -1): items.append((lvl[k], st))
        t = b + fade
    if total and total > t: items.append((blank, total-t))
    lst = os.path.join(work, "scrim.txt")
    with open(lst, "w") as f:
        for p, d in items:
            f.write("file '%s'\nduration %.3f\n" % (p.replace("'","'\\''"), max(0.02, d)))
        f.write("file '%s'\n" % items[-1][0].replace("'","'\\''"))
    subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",lst,
        "-r",str(fps),"-c:v","qtrle","-pix_fmt","argb",out], check=True)
    return out
