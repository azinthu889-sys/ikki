#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · ရောင်ခြယ်ခြင်း (grade)。

⚠️ ဤကိန်းများကို Zin ရဲ့ `zin_japan_life.yaml` playbook (grade v3) မှ
   ယူထားသည် — မှန်းချက် မဟုတ်、verified_result ပါပြီးသား
   (skin IRE ၃၈.၃ · scene median ၅၇.၄ · skin/scene ၁.၇)。

⚠️ **curve ရဲ့ အလယ်မှတ်ကို ၀.၄၀ အောက် မချရ** — အသားအရောင်က အဲဒီမှာ
   နေသည်。 မှောင်ချင်လျှင် vignette တင်ရမည်၊ curve မချရ (playbook note)。

⚠️ grade ကို **ရုပ်ပေါ်မှာသာ** ချရသည် — စာတန်း/ဂရပ်ဖစ် အပေါ် ချလျှင်
   အဖြူစာက မွဲပြီး stroke က ပျက်သည်。 ⇒ ဖြတ်ပြီးသော ဗီဒီယိုပေါ် ချပြီးမှ
   overlay တင်ရသည်。
"""
import os, subprocess

# playbook ရဲ့ base (grade v3)
LEVELS = dict(imin=0.145, imax=0.72, omin=0.075, omax=1.0)
CURVE  = "0/0 0.16/0.10 0.40/0.40 0.68/0.80 1/1"
CBAL   = dict(rm=0.0, gm=0.035, bm=-0.03, rh=0.01, gh=0.03, bh=-0.045)

def chain(rc):
    """recipe အလိုက် ffmpeg filter chain — မလိုလျှင် None"""
    if not rc.get("grade", True): return None
    sat  = rc.get("sat")
    vign = rc.get("vign")
    if sat is None and vign is None: return None
    sat  = 1.05 if sat is None else float(sat)
    vign = 0.60 if vign is None else float(vign)
    # ⚠️ base levels က **ZJL ရဲ့ မှောင်တဲ့ အခန်း** (mean ၄၁–၅၀) အတွက်。
    #    ZAE ရဲ့ အဖြူနံရံ studio (mean ၂၁၄) ပေါ် ချလျှင် imax=0.72 က
    #    ၁၈၄ အထက် အကုန် အဖြူ လုပ်ပြီး frame ရဲ့ **၂၈.၆%** ပြတ်သွားသည်
    #    (reference က ၈.၈% သာ — တကယ် ဖြစ်ခဲ့、Zin က "ကြောင်တောင်တောင်"
    #    ဟု ပြောခဲ့သည်)。 ⇒ recipe က levels ကို override လုပ်နိုင်ရမည်。
    L = dict(LEVELS)
    for k in ("imin", "imax", "omin", "omax"):
        v = rc.get("lv_" + k)
        if v is not None: L[k] = float(v)
    parts = [
      ("colorlevels="
       f"rimin={L['imin']}:gimin={L['imin']}:bimin={L['imin']}:"
       f"rimax={L['imax']}:gimax={L['imax']}:bimax={L['imax']}:"
       f"romin={L['omin']}:gomin={L['omin']}:bomin={L['omin']}:"
       f"romax={L['omax']}:gomax={L['omax']}:bomax={L['omax']}"),
    ]
    # ⚠️ curve="none" = **curve လုံးဝ မထည့်**。 ZAE ရဲ့ အဖြူနံရံ studio မှာ
    #    curve က အလင်းကို ထပ်မြှင့်ပြီး frame ရဲ့ ၂၈% ပြတ်သွားသည်
    #    (sweep ဖြင့် တိုင်းရွေး)。
    #
    # ⚠️ **ပစ်မှတ်ကို frame အပြည့်နဲ့ မတိုင်းရ** — N5 reference ရဲ့ "ပြတ် ၉.၂%"
    #    ဟာ အများစု **စာတန်းအဖြူ** ဖြစ်နေသည်。 ပုံအပိုင်း (အပေါ် ၅၅%) ချည်း
    #    တိုင်းလျှင် N5 = **၀.၈%** သာ。 ဒီအမှားကြောင့် imax ကို ၀.၉၄ ထား
    #    ဖြစ်ပြီး ပုံထဲ ၁၀.၃% ပြတ်သွားသည် ("အလင်းများလွန်း · ကြောင်တောင်တောင်")。
    # ⇒ ZAE မှာ **imax=1.0 · omin=0.0** — အလင်းကို လုံးဝ မဆွဲတင်၊
    #    contrast ကို အောက်ပိုင်း (imin) ကနေသာ ယူသည် → ပြတ် ၁.၂%。
    _cv = rc.get("curve", None)
    _cv = CURVE if _cv is None else _cv
    if _cv and _cv != "none":
        parts.append(f"curves=all='{_cv}'")
    parts += [
    ]
    # ⚠️ brand_review မှာ colorbalance **ပိတ်ရမည်** — ပစ္စည်းရဲ့ အရောင်
    #    အစစ်ကို ပြရမည် (playbook: "Grade က အရောင်ကို လှည့်ပစ်ရင်
    #    သုံးသပ်ချက် လိမ်သွားသည်")。
    if rc.get("cbal", True):
        c = CBAL
        parts.append("colorbalance="
            f"rm={c['rm']}:gm={c['gm']}:bm={c['bm']}:"
            f"rh={c['rh']}:gh={c['gh']}:bh={c['bh']}")
    # ⚠️ ZAE မှာ **colorbalance ပိတ် · vignette ပိတ် · sat 1.00**。
    #    N5 reference ရဲ့ ပြောသူ shot ကို crop ပြီး တိုင်းတော့
    #      mean ၂၂၀ · p05 ၉၂ · ပြတ် ၀.၁% · sat ၆.၉
    #    မူရင်း footage က crop ပြီးရင် ၂၂၄ · ၁၁၇ · ၀.၀ · ၄.၆ —
    #    **နီးနီးလေး ဖြစ်နေပြီး** grade ပါးပါးသာ လိုသည်。
    #    colorbalance က အဖြူနံရံကို အရောင်ဆိုးပြီး sat ကို ၁၅ အထိ
    #    တင်သည် (ပစ်မှတ် ၆.၉)。 vignette ကတော့ ထောင့်/အလယ် အချိုးကို
    #    ၁.၃၅ → ၁.၁၁ ချသည် — N5 က ၁.၃၅၇ · မူရင်း ၁.၃၆၈ ⇒ **N5 မှာ
    #    vignette လုံးဝ မရှိ** (တိုင်း၍ အတည်ပြုပြီး)。
    parts.append(f"eq=saturation={sat}")
    if vign > 0: parts.append(f"vignette=a={vign}")
    return ",".join(parts)

def apply(src, out, rc, log=print):
    fc = chain(rc)
    if not fc:
        log("  grade မလုပ် (recipe မှာ မသတ်မှတ်)")
        return src
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-vf",fc,
        "-c:v","h264_videotoolbox","-b:v","16M","-c:a","copy",out], check=True)
    log(f"  grade v3 · sat {rc.get('sat',1.05)} · vignette {rc.get('vign',0.60)}"
        + ("" if rc.get("cbal", True) else " · colorbalance ပိတ်"))
    return out
