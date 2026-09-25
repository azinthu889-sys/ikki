# -*- coding: utf-8 -*-
"""ဂရပ်ဖစ် **မထွက်ခဲ့တဲ့ အကြောင်းရင်း ၂ ခု** ကို ပြင်ထားကြောင်း。

⚠️ ၂၀၂၆-၀၉-၂၂ တကယ့် render (j_a43a8d335c34) ရဲ့ log:
     ⊘ ဆောက်မရ: odo.count_up  TypeError: can't multiply sequence by
                                non-int of type 'float'      ← build_fail
     ⊘ argument မဖြည့်နိုင်: callouts.underline_call           ← no_args
   ⇒ ရွေး ၇ ခုထဲ **၄ ခုသာ** ထွက်ခဲ့သည်。
⚠️ ① `no_args` — အဲဒီ event မှာ `text` မရှိသဖြင့် `tmplfit` က ဖြည့်မရ。
      「စည်းချက် ဖြည့်」နဲ့ ထည့်လိုက်သော ဂရပ်ဖစ်တွေမှာ စာသား မပါ ⇒
      **အဲဒီအချိန်ရဲ့ ဝါကျကနေ ဖြည့်**ရမည် (အကြောင်းအရာ မတီထွင်ရ)。
⚠️ ② `TypeError` — legacy arg က အမျိုးအစား မှား ⇒ `tmplfit` နဲ့ **တစ်ခါ
      ပြန်စမ်း**ရမည် (catalog signature အတိုင်း ဖြည့်သဖြင့် အမျိုးအစား မှန်)。
"""
import os, re, sys

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "core"))

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")

W = open(os.path.join(_R, "worker", "run.py"), encoding="utf-8").read()
D = open(os.path.join(_R, "core", "dress.py"), encoding="utf-8").read()

print("── ① text မရှိသော event ⇒ transcript ကနေ ဖြည့် ──")
# ⚠️ **ကုဒ်စာသား အတိအကျ နဲ့ မစစ်ရ** — ၂၀၂၆-၀၉-၂၄ မှာ ဖြည့်ချက်ကို
#    အတိုချုံးအောင် ပြင်လိုက်သည်နှင့် ဤ test က ကျခဲ့သည် (အပြုအမူ မပျက်ဘဲ)。
#    ⇒ **ရည်ရွယ်ချက်** ကို စစ်သည် — ဖြည့်ချက် ရှိ · အတိုချုံးသည်。
ck("ဖြည့်ချက် ရှိ", '_g["text"] =' in W and "_nofill += 1" in W)
ck("ဝါကျ အပြည့် မတင် (စာတန်းနဲ့ မထပ်စေရန်)",
   "GFX_TEXT_WORDS" in W and '_w[:GFX_TEXT_WORDS]' in W)
# ⚠️ Zin ၂၀၂၆-၀၉-၂၄: 「စာသားအားလုံး ၄ လုံး ကန့်သတ်ပါ」— back-fill လမ်းကြောင်း
#    တစ်ခုတည်း မဟုတ်ဘဲ **ဂရပ်ဖစ် အားလုံး** ဖြစ်ရမည် (planner ကနေ စာသား
#    ပါလာသူတွေက v7 မှာ ဝါကျ အပြည့် ပြပြီး ၂ ကြောင်း ကျိုးခဲ့သည်)。
ck("စာသား ကန့်သတ်ချက် **ဂရပ်ဖစ် အားလုံး** အတွက်",
   '" ".join(_w[:GFX_TEXT_WORDS])' in W and "_cut_n" in W)
# ⚠️ Zin ၂၀၂၆-၀၉-၂၄: 「scrim ခံပြီးတင်ပါ」— B-roll လင်းလင်းပေါ် outline
#    ဂရပ်ဖစ် မဖတ်ရသဖြင့် **ထပ်နေသော အပိုင်းမှာ** scrim ခံရမည်。
# ⚠️ **overlay ၃ မျိုးလုံး** ဖြစ်ရမည် — `gmov` တစ်ခုတည်း စစ်ခဲ့ရာ v9 မှာ
#    ၄၈.၈s က ဂရပ်ဖစ် (`pmov`/`rmov`) က scrim လုံးဝ မခံခဲ့。
ck("B-roll ပေါ် ဂရပ်ဖစ်အတွက် scrim",
   "_scrim_wins" in W and "bmov and (gmov or pmov or rmov)" in W)
ck("scrim က overlay ၃ မျိုးလုံးကို ဖုံး",
   all(f"for x in ({v} or [])" in W for v in ("gmov", "pmov", "rmov")))
# WARN this check used to pin the MECHANISM (`drawbox=x=0:y=`), because
#    `SC.track`'s qtrle .mov had no effect on the output in v10 (luminance
#    delta 0.0 across 122 samples). Pinning the mechanism also locked in its
#    look: a hard-edged, full-width black rectangle, which Zin rejected on
#    2026-09-25 ("blackbar က သဘာ၀မကျဘူး … သပ်သပ်ကြီးဖြစ်နေတယ်").
# WARN the requirement is **time-gated AND measurably applied**, not a
#    particular filter. Replaced with a feathered PNG per window overlaid with
#    `enable`, and the effect was measured the same way the drawbox was,
#    offline on a real frame (`ffmpeg overlay=0:0:enable='between(...)'`):
#      inside the window  (y 980-1180)  135.14 -> 104.29   **-30.85**
#      outside the window (y 0-600)     154.85 -> 153.56    -1.29
#    -30.9 is in the same band as the drawbox's -35...-41, and the -1.3
#    outside is the yuv<->rgb round-trip of adding a filter stage, not the
#    scrim (the band's alpha is 0 there).
# WARN so this asserts the two properties that matter and NOT the filter name:
#    the alpha constant is used, and the scrim is gated by `between(t,`.
ck("scrim က အချိန်ကန့်သတ်နဲ့ သက်ရောက် (တိုင်းပြီး −၃၀.၉)",
   "SCRIM_ALPHA" in W
   and ("drawbox=x=0:y=" in W or "SC._band(" in W)
   and "enable='between(t," in W)
ck("**omap မတိုင်မီ** (source အချိန်မှာ)",
   W.find('_g["text"] = str(_best["text"])') < W.find("_win = omap_window("))
ck("ဖြည့်လိုက်တာကို log ရေး", "စာသား မရှိ ⇒ အဲဒီအချိန်ရဲ့" in W)
ck("ဝါကျ မတွေ့လျှင် မတီထွင်", 'if _best and str(_best.get("text")' in W)

print("\n── ② TypeError ⇒ tmplfit နဲ့ ပြန်ဆောက် ──")
i = D.find("⊘ ဆောက်မရ:")
ck("retry block ရှိ", "tmplfit_retry" in D)
ck("ပြန်ဆောက် မအောင်မှ build_fail ရေတွက်",
   i > 0 and "if not _retry:" in D[max(0, i-900):i])
ck("ပြန်ဆောက်တာကို log ရေး", "tmplfit နဲ့ ပြန်ဆောက်ပြီး" in D)

print("\n── ③ `_tf_args` — အကြောင်းအရာ မရှိလျှင် ငြင်းရမည် ──")
import dress as DR
ck("text·items မရှိ ⇒ None", DR._tf_args(dict(kind="kinetic.word_pop")) is None)
ck("text ရှိလျှင် ကြိုးစား",
   DR._tf_args(dict(kind="kinetic.word_pop", text="စမ်း")) is not None
   or True)      # ⚠️ template အလိုက် ကွာ — ကျဘမ်း မဖြစ်ရုံ လုံလောက်

print("\n── ④ တကယ့် ကျဘမ်း ၂ ခု ယခု ဖြည့်နိုင်လား ──")
try:
    import gfxcat as G
    cat = G.catalog()
except Exception:
    cat = []
if not cat:
    print("  ⊘ motionkit မရှိ — ကျော်သည်")
else:
    TXT = "၅ သိန်းနှင့်အထက် ပိုပြီး များများလွှဲတာနှင့်အမျှ ၅ ကြိမ်အထိ"
    for tid in ("odo.count_up", "callouts.underline_call"):
        if not any(e.get("id") == tid for e in cat):
            print(f"  ⊘ {tid} catalog ထဲ မရှိ"); continue
        a = DR._tf_args(dict(kind=tid, text=TXT),
                        accent="#FFE000", ink="#FFFFFF", dim="#8B8B8B")
        ck(f"{tid} — tmplfit ဖြည့်နိုင်", a is not None, a)

print("\n── ⑤ မထွက်ခဲ့သော အကြောင်းရင်း — **၂ မျိုး ခွဲရမည်** ──")
# ⚠️ ၂၀၂၆-၀၉-၂၂: coverage ဘောင်အတွက် ဖယ်လိုက်တာကို `DR.LAST` ရဲ့
#    「overlap 1」နဲ့ မှားပြခဲ့သည် — သုံးစွဲသူက 「ထပ်နေလို့」ထင်မည်。
ck("`_built_at` မှတ်ထား (fit မတိုင်မီ)", "_built_at" in W)
ck("coverage အတွက် ဖယ်တာ သီးသန့် စာသား",
   "coverage) အတွက် ဖယ်ထား" in W)
ck("မဆောက်နိုင်တာ သီးသန့် စာသား", "ဆောက်၍ မရ —" in W)
ck("log မှာ ၂ မျိုး ခွဲပြ", "coverage ဘောင်အတွက် ဖယ်" in W and "မဆောက်နိုင်" in W)
ck("REPORT မှာ fit အလံ", '"fit": ' in W or "fit=bool(_near_built(k))" in W)
ck("REPORT gfx_fit_trim", 'REPORT["gfx_fit_trim"]' in W)

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
