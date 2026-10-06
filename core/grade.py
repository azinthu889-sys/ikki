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
try:
    from video_codec import h264_args
except ImportError:  # Allows direct package imports in development tools.
    from core.video_codec import h264_args

# playbook ရဲ့ base (grade v3)
LEVELS = dict(imin=0.145, imax=0.72, omin=0.075, omax=1.0)
CURVE  = "0/0 0.16/0.10 0.40/0.40 0.68/0.80 1/1"
CBAL   = dict(rm=0.0, gm=0.035, bm=-0.03, rh=0.01, gh=0.03, bh=-0.045)

# ── သဘာဝ mode (၂၀၂၆-၀၉-၂၀ · Zin: "သဘာ၀အကျဆုံး · အလင်းအမှောင်မှန်ပါစေ") ──
# C0088 ရဲ့ frame ၁၂ ခုကို chain တစ်ခုချင်း ဖြတ်ပြီး တိုင်းရွေးထားသည် —
#   မူရင်း   : ဖြူဖြတ် ၀.၀၀% · မည်းဖြတ် ၀.၀၀% · p05 ၃၅ · အလယ် ၁၀၀ · p95 ၁၄၂ · G−B +၁.၆
#   ယခင် ZJL : ဖြူဖြတ် ၀.၀၀% · မည်းဖြတ် **၁.၂၂%** · p05 **၆** · အလယ် ၉၂ · p95 ၁၉၁ · G−B **+၁၅.၅**
#   သဘာဝ     : ဖြူဖြတ် ၀.၀၀% · မည်းဖြတ် ၀.၀၀% · p05 ၃၁ · အလယ် ၁၀၂ · p95 ၁၄၈ · G−B **+၁.၈**
# ⇒ အရိပ်ထဲ အချက်အလက် မပျောက်、အရောင် မလှည့်、contrast ပါးပါးသာ တင်သည်。
#
# ⚠️ `eq=saturation` က **မူရင်းမှာ ရှိပြီးသား အရောင်စောင်းကို ချဲ့ပေးသည်** —
#    ၁.၀၂ တင်ရုံနဲ့ G−B က +၁.၈ ကနေ **+၆.၃** တက်သွားသည် (တိုင်းပြီး)。
#    ⇒ သဘာဝ mode မှာ sat = ၁.၀ · eq ကို လုံးဝ မထည့်。
# ⚠️ `recipes.py` ကနေ ယူသည် — အဲဒီဖိုင်က API image ထဲ ပါပြီး ဒီဖိုင် မပါ。
#    ဒီမှာ သတ်မှတ်လျှင် `/api/styles` ပျက်သည် (၂၀၂၆-၀၉-၂၀ တကယ် ဖြစ်)。
try: from recipes import NATURAL
except ImportError: from core.recipes import NATURAL

# ══ premium look (Zin ၂၀၂၆-၁၀-၀၆ 「Color grading သေချာလုပ်」) ══════════════
# j_d96beb16229d (yuvj420p · flat · အစိမ်းစောင်း) မှာ ယခင် lift က အနက်ကိုပါ
# ဆွဲတင်ပြီး **နို့ရည်ရောင်** — sweater Y ၄၅ → ၆၃ · skin ၁၃၃/၁၂၄/၁၁၃ → ၁၈၀/၁၇၁/၁၅၇
# (ဖြူဖျော့)。 premium ⇒ အနက် **နက်နက်** (×၀.၇၅ knee) · အသားရေကို ပစ်မှတ်ရဲ့ ၆၄%
# သာ တင် · highlight roll-off · နွေး ၅၆၀၀K mix ၀.၄၀ · vibrance (အသားရေ မထိ
# စေရန် sat မဟုတ်) · vignette ပါးပါး。 တိုင်းချက် (frame ၂၆s):
#   မူရင်း  skin 133/124/113 (R−G 9) · sweater 45 · wall 144/146/148 · p02 33
#   ယခင်    skin 180/171/157 (R−G 9) · sweater 63 · wall 188/192/193 · p02 40
#   premium skin 161/143/124 (R−G 18) · sweater 42 · wall 148/144/141 · p02 20
PREMIUM_LOOK = "colortemperature=temperature=5600:mix=0.40,vibrance=intensity=0.28,vignette=a=0.30"


def _premium_lut(sk, tg):
    tgt = sk + 0.64 * (tg - sk)
    bk = min(36.0, sk * 0.47)
    hi_x, hi_y = 190.0, 219.0
    if not (bk + 4 < sk < hi_x - 10):
        return ""
    return ("lutyuv=y='"
            f"if(lt(val,{bk:.1f}),val*0.75,"
            f"if(lt(val,{sk:.1f}),{bk*0.75:.2f}+(val-{bk:.1f})*{(tgt-bk*0.75)/(sk-bk):.5f},"
            f"if(lt(val,{hi_x:.1f}),{tgt:.2f}+(val-{sk:.1f})*{(hi_y-tgt)/(hi_x-sk):.5f},"
            f"{hi_y:.1f}+(val-{hi_x:.1f})*{(255.0-hi_y)/(255.0-hi_x):.5f})))'")


def look_filter(rc):
    """premium look (RGB) — **အဆုံးမှာ တစ်ခါတည်း** ထည့်ရမည် (အပိုင်းလိုက် မဟုတ် ·
    yuv↔rgb အသွားအပြန် မပွားစေရန် — `luma_filter` မှတ်ချက် ကြည့်)。"""
    return PREMIUM_LOOK if rc.get("grade_look") == "premium" else ""


def luma_filter(rc):
    """အသားရေ အလင်း — premium ဆိုလျှင် အနက် နက်စေသော lut、မဟုတ်လျှင် ယခင်အတိုင်း。"""
    if rc.get("grade_look") == "premium":
        _ll = rc.get("luma_lift")
        try:
            if not _ll or len(_ll) < 2:
                return ""
            _sk, _tg = float(_ll[0]), float(_ll[1])
        except (TypeError, ValueError):
            return ""
        if not (8.0 < _sk < 240.0 and _tg > _sk + 4.0):
            return ""
        return _premium_lut(_sk, _tg)
    return _luma_only(rc)


def _luma_only(rc):
    """အသားရေ အလင်း တင်ရန် `lutyuv` တစ်ကြောင်း — မလိုလျှင် `""`

    ⚠⚠ **ဒါက YUV filter** ⇒ RGB filter (`colorlevels`/`curves`) ကြားမှာ
       ထည့်လျှင် ffmpeg က **yuv↔rgb အသွားအပြန်** တစ်ခါ ထည့်သည်。
       အပိုင်းလိုက် grade (`shotlook.windowed`) မှာ အပိုင်းတိုင်းအတွက်
       ထည့်ခဲ့ရာ အသွားအပြန် **၅ ခါ** ဖြစ်ပြီး အသားရေ G−B ကို
       **၇.၃ → ၁၂.၅** တင်ခဲ့သည် (၂၀၂၆-၁၀-၀၁ တိုင်း၍ တွေ့ · အပိုင်း ၁ ခု
       ၇.၃၀ · ၂ ခု ၈.၇၅ · ၅ ခု ၁၂.၄၅ — filter တူတူ、ဝင်းဒိုး ကွာရုံ)。
       ကိန်းက **တစ်ခုတည်း** (skin Y တစ်ခါ တိုင်း → ပစ်မှတ် တစ်ခု) ဖြစ်၍
       အပိုင်းလိုက် ထည့်စရာ **အကြောင်း မရှိ** ⇒ ခေါ်သူက `lift=False` နဲ့
       အပိုင်းတွေ ဆောက်ပြီး ဒီ filter ကို **အဆုံးမှာ တစ်ခါတည်း** ထည့်ရမည်。
       (`eq` ကလည် တူညီသော ကုန်ကျစရိတ် ရှိ၍ sat ၁.၀ မှာ မထည့်ပါ — အောက်
        မှတ်ချက် ကြည့်)。
    """
    _ll = rc.get("luma_lift")
    if not _ll:
        return ""
    try:
        # ⚠️ အရှည် ၂ မဟုတ်လျှင် `IndexError` — အောက်က except မှာ
        #    မပါခဲ့၍ grade တစ်ခုလုံး ကျမည် (ကိုယ့် test က ဖမ်းမိသည်)。
        if len(_ll) < 2:
            return ""
        _sk, _tg = float(_ll[0]), float(_ll[1])
        if not (8.0 < _sk < 240.0 and _tg > _sk + 4.0):
            return ""
        # ⚠️ အနက် knee — မထားလျှင် အောက်ပိုင်း အကုန် ဆွဲတက်ပြီး
        #    နို့ရည်ရောင် ဖြစ်သည် (p05 ၃၄ → ၉၀)。
        _sx, _sy = 20.0, 20.0 * 1.28
        _bx = (_sk + 255.0) / 2.0
        _by = min(250.0, (_tg + 255.0) / 2.0 + 10.0)
        return ("lutyuv=y='"
                f"if(lt(val,{_sx:.1f}),val*{_sy/_sx:.5f},"
                f"if(lt(val,{_sk:.1f}),{_sy:.1f}+(val-{_sx:.1f})*"
                f"{(_tg-_sy)/(_sk-_sx):.5f},"
                f"if(lt(val,{_bx:.1f}),{_tg:.1f}+(val-{_sk:.1f})*"
                f"{(_by-_tg)/(_bx-_sk):.5f},"
                f"{_by:.1f}+(val-{_bx:.1f})*{(255.0-_by)/(255.0-_bx):.5f})))'")
    except (TypeError, ValueError, ZeroDivisionError, IndexError, KeyError):
        return ""


def chain(rc, lift=True):
    """recipe အလိုက် ffmpeg filter chain — မလိုလျှင် None"""
    if not rc.get("grade", True): return None
    # သဘာဝ mode — recipe က သီးသန့် မသတ်မှတ်ထားသော ကိန်းတိုင်းကို ဖြည့်ပေးသည်
    # ⚠️ **အပြည့် override** ဖြစ်ရမည် — "မရှိမှ ဖြည့်" လုပ်လျှင် `cbal`/`sat` က
    #    DEF ကနေ တန်ဖိုး ရပြီးသား ဖြစ်၍ ဘယ်တော့မှ မဝင်、colorbalance နဲ့
    #    sat ၁.၀၅ ကျန်နေမည် (တိုင်းစစ်၍ တွေ့)。 look ကွဲချင်သော recipe က
    #    `natural=False` ထားပြီး ကိုယ့်ကိန်း ကိုယ် ထားရမည်。
    # `recipes.get()` က ဖြန့်ပြီးသား ဖြစ်သင့်သည် — ဒီမှာက raw dict နဲ့
    # တိုက်ရိုက် ခေါ်လျှင် အတွက်သာ (မရှိမှ ဖြည့်၊ ရှိတာ မထိ)。
    if rc.get("natural"):
        rc = dict(rc)
        for k, v in NATURAL.items():
            if rc.get(k) is None: rc[k] = v
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
    # ⚠️ **အသားအရောင် လိုက်ဖက်စေရန် gamma** (၂၀၂၆-၀၉-၁၇ Zin: "မျက်နှာ အရမ်း မဲနေတယ်")。
    #    တိုင်းချက် — tokutei (နောက်ကွယ် ကောင်းကင် လင်းနေသော backlit shot) မှာ
    #    မူရင်း skin Y ၁၅၇ ⇒ IKKI ထွက် **၁၄၅** (−၁၀ ~ −၁၆)。 အကြောင်းရင်းက
    #    `colorlevels` ရဲ့ `imin` ၀.၁၀ — အဲဒါ ZAE ရဲ့ **အဖြူနံရံ studio** အတွက်
    #    တိုင်းထားတာ ဖြစ်ပြီး အပြင်မှာ ရိုက်သော shot မှာ မျက်နှာကို ချသည်。
    #    ⇒ worker က skin Y တိုင်းပြီး `gamma` ပေးလျှင် ဒီမှာ တင်သည် (ပုံသေ မပါ)。
    # ══ အသားရေ အလင်း — **luma သာ** (chroma မထိ) ═══════════════════
    # ⚠️⚠️ `curves=all` (RGB ၃ ခုစလုံး) နဲ့ တင်လျှင် **အရောင် လွဲသည်**。
    #    အသားရေမှာ R > G > B ဖြစ်၍ မတ်စောက်သော အပိုင်းက ခြားနားချက်ကို
    #    ချဲ့ပြီး hue နဲ့ saturation ၂ ခုလုံး ရွှေ့သည် — တိုင်းချက်:
    #      မူရင်း   skin G−B **−8.5** · Cr **138.4**
    #      RGB curve skin G−B **−17.2** · Cr **147.0**  ⇒ ခရမ်း/နီ ဘက် လွဲ
    #      luma သာ  skin G−B **−8.8**  · Cr **138.5**  ⇒ **မပြောင်း** ✓
    #    (၂၀၂၆-၀၉-၂၉ Zin:「မင်းကာလာကစောက်တလွဲဖြစ်နေတယ်」 — သူ မှန်သည်、
    #     ငါ အစိမ်းကို ဖယ်ရင်း **ခရမ်း ထည့်**မိခြင်း)。
    # ⇒ `lutyuv` နဲ့ **Y တစ်ခုတည်း** ကို ရွှေ့သည် — U/V မထိ ⇒ hue/sat
    #   အတိအကျ ကျန်သည်。
    if lift:
        _lf = luma_filter(rc)
        if _lf:
            parts.append(_lf)
        _lk = look_filter(rc)
        if _lk:
            parts.append(_lk)
    g = rc.get("gamma")
    if g:
        g = max(0.85, min(1.30, float(g)))
        parts.append(f"eq=gamma={g:.3f}:saturation={sat}")
    elif abs(sat - 1.0) > 1e-6:
        # sat ၁.၀ ဆိုလျှင် eq ကို လုံးဝ မထည့် — YUV အသွားအပြန်က
        # G−B ကို +၁.၆ ⇒ +၁.၂ ချသည် (တိုင်းပြီး)。 filter မထည့်တာက တိကျသည်。
        parts.append(f"eq=saturation={sat}")
    if vign > 0: parts.append(f"vignette=a={vign}")
    return ",".join(parts)

def apply(src, out, rc, log=print):
    fc = chain(rc)
    if not fc:
        log("  grade မလုပ် (recipe မှာ မသတ်မှတ်)")
        return src
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-vf",fc,
        *h264_args("16M", crf=18),"-c:a","copy",out], check=True)
    log(f"  grade v3 · sat {rc.get('sat',1.05)} · vignette {rc.get('vign',0.60)}"
        + ("" if rc.get("cbal", True) else " · colorbalance ပိတ်"))
    return out
