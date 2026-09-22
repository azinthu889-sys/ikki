#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · recipe — ဤအလွှာက product ဖြစ်သည်。

⚠️ stage တွေက အတူတူပဲ။ ဘယ် stage ဘယ်လောက် သုံးလဲ ဆိုတာက ထွက်လာမယ့် ပုံစံ
   ဆုံးဖြတ်သည်。 recipe အသစ် ထည့်ရန် **ကုဒ် မရေးရ** — ဤဇယားထဲ ထည့်ရုံ。

⚠️ cut_aggression က ပုံသေ မဖြစ်ရ — Podcast မှာ အနားယူချိန် ဖြတ်တာ မှန်ပေမယ့်
   သင်ခန်းစာမှာ အနားယူချိန်က ကျောင်းသား စဉ်းစားတဲ့နေရာ。 Cinematic မှာလည်း
   အသက်ရှုသံနဲ့ တိတ်ဆိတ်မှုက ခံစားချက် ဖြစ်စေသည်。
"""
# ⚠️ cap_pct  = စာတန်း အရွယ် (frame အမြင့်၏ %)
#    cap_base = စာတန်း အောက်စွန်း ဘယ်နေရာ (frame အမြင့်၏ %)
#    stroke   = စာတန်း အနားသတ် — ZAE ရဲ့ **အထင်ရှားဆုံး** အချက်。
#               အဖြူ studio wall ရော အမှောင် B-roll ရော ဖတ်လို့ရစေရန်。
#    lufs     = အသံအဆင့် — ZAE က feed video မို့ ZJL ထက် တိတ်သည်
R = {
 # ── ZJL · ZIN JAPAN LIFE — Zin ရဲ့ frame-by-frame spec မှ **တိုင်းယူထားသည်** ──
 #    System A captions: အဖြူ **Regular (bold မဟုတ်)** · cap-height 2.6% of H
 #    (cap က em ရဲ့ တစ်ဝက်မို့ size = H × 0.052) · **box မရှိ · stroke မရှိ ·
 #    shadow ချည်းသာ** · baseline 68% of H · တစ်ကြောင်းတည်း ~၂၈ cluster
 #    −14 LUFS · −1.0 dBTP · bed sidechain 4:1
 #    font: **Masterpiece Uni Round** — Zin ကိုယ်တိုင် ရွေးထားသည်၊ မပြောင်းရ
 "cinematic-vlog": dict(label="Cinematic Vlog", theme="zjl", fps=24,
    keep_pause=0.55, min_sil=1.20, captions="light", gfx=3, music="folk",
    mmf="MasterpieceUniRound", latin="Figtree",
    cap_pct=0.0426, cap_base=0.680, stroke=None, stroke_w=0.0,
    lufs=-15.0, cap_max=0.833, scrim=False, broll=4,
    broll_pct=0.45, cap_cover=0.30,
    # ⚠️ ဒါက **တမင် cinematic** ဖြစ်၍ natural မလုပ်ပါ (colorbalance/vignette ကျန်)。
    #    ဒါပေမယ့် ZJL base levels က အရိပ်ကို ၁.၂၂% ချေမှုန်းသည် (p05 ၆) ⇒
    #    levels/curve ကို သဘာဝ ကိန်းနဲ့ လဲပြီး **ချေမှုန်းမှု ၀** ထားသည်。
    lv_imin=0.03, lv_imax=0.97, lv_omin=0.02, lv_omax=1.0,
    curve="0/0 0.25/0.245 0.50/0.51 0.75/0.765 1/1",
    # ⚠️ vignette ၀.၆၅ က ထောင့်သာ မဟုတ်、**frame တစ်ခုလုံးကို** မှောင်စေသည် —
    #    အလယ်တန်း ၁၀၄ ⇒ ၇၂ (မူရင်း ၁၀၀)。 sweep တိုင်းချက်:
    #    ၀.၂၀→၁၀၀ · ၀.၃၀→၉၅ · ၀.၄၅→၈၆ · ၀.၆၅→၇၂  ⇒ ၀.၂၀ က မူရင်းနဲ့ တိတိကျကျ။
    sat=1.02, vign=0.20, sfx_per_min=1.0),
 "vlog": dict(label="Vlog", theme="zjl", fps=30,
    keep_pause=0.40, min_sil=0.75, captions="karaoke", gfx=6, music="upbeat",
    mmf="MasterpieceUniRound", latin="Figtree-Black",
    cap_pct=0.0481, cap_base=0.680, lufs=-14.5, cap_max=0.833, scrim=False,
    broll=5, broll_pct=0.30, cap_cover=0.85,
    natural=True,   # သဘာဝ grade (၂၀၂၆-၀၉-၂၀)
    sat=1.05, vign=0.55, sfx_per_min=1.0),
 "podcast": dict(label="Podcast", theme="zjl", fps=30,
    # ⚠️ **High-Retention Talking-Head** (Zin ၂၀၂၆-၀၉-၂၀ · ref `KCN4-2hyUBM`
    #    နှင့် `01BnhfTaQoo` — creator တူ)。 တိုင်းချက်: စာသား ၄၆%၊ အောက်ပိုင်း
    #    ၁၄% ⇒ **burned-in စာတန်း မသုံး**。 keyword pop နဲ့ ဘောင်အပြည့် ကတ်သာ。
    #    accent #E5BC32 (frame ၃ ခုမှ တိုင်း — ZJL ရဲ့ #FFE000 နဲ့ RGB ၁၁၂ ကွာ)。
    cap_typo=0.22, accent="#E5BC32", insert_per_min=2.5,
    keep_pause=0.26, min_sil=0.45, captions="karaoke", gfx=2, music=None,
    mmf="MasterpieceUniRound", latin="Figtree",
    cap_pct=0.0444, cap_base=0.680, lufs=-14.0, cap_max=0.833, scrim=False,
    natural=True,   # သဘာဝ grade (၂၀၂၆-၀၉-၂၀)
    sat=1.03, vign=0.45, sfx_per_min=0.3),
 # ── Knowledge Sharing — Zin ပေးသော reference ၂ ခု (၉.၂ + ၁၀.၉ မိနစ်) မှ
 #    **တိုင်းယူထားသည်**。 1920×1080 · 30fps · bt709。
 #    ⚠️ ဒီပုံစံရဲ့ အထင်ရှားဆုံး အချက် — **စာတန်းက အားလုံး မပေါ်ဘူး**。
 #       reference မှာ frame ရဲ့ ၁၀% နှင့် ၁၇% ပဲ စာတန်း ပါသည် (slide မပါ)。
 #       ⇒ cap_cover က အဲဒါ。 အားလုံး ချလျှင် ဒီပုံစံ မဖြစ်ဘူး。
 #    ⚠️ စာတန်း အရွယ် **၂.၄% of H** ပဲ — ZAE ရဲ့ ၈% နှင့် ZJL ရဲ့ ၅.၂% ထက်
 #       အများကြီး သေးသည် (တိုင်းချက်: အဖြူ ၁.၉–၂.၉% · အနီ/ရွှေ အလေးထား ၃.၈%)。
 #    ⚠️ ဖြတ်မှု — reference မှာ −၃၁dB ဖြင့် ၀.၂s အထက် တိတ်ဆိတ်မှု **၀ ခု**
 #       (အနားယူချိန် ဖြုတ်ပြီးသား)。 ⇒ tight。 shot ဖွဲ့စည်းမှုက bimodal:
 #       ≥၁၀s shot တွေက အချိန် **၇၈–၇၉%** စားသည်、<၃s တွေက ၄၉–၆၇% (အရေအတွက်)。
 #    အသံ: −14.9 LUFS · LRA ၂.၈–၃.၉ LU (compress ပြင်းထန်သော narration)
 #    grade: အမှောင် low-key · mean lum ၄၁–၅၀/၂၅၅ · black ၁–၂ (ချေထား) ·
 #           highlight ၁၃၂–၁၄၁ · နွေး R−B +၁၂…+၂၈ · ရောင်စဉ် ၂၈–၃၉%
 # ══ reference ၃ ပုဒ်မှ တိုင်းပြီး ဆောက်ထားသော style ၃ ခု ══════════
 #    တိုင်းချက် → `assets/calib/ref_hype_2026.json` (၂၀၂၆-၀၉-၂၀)。
 # ⚠️ **ပုံစံ ၃ မျိုး ကွဲသည် — ပျမ်းမျှ မယူရ** ဟု တိုင်းချက်က ပြသည်。
 # ⚠️ ၃ ပုဒ်လုံး တိတ်ဆိတ်မှု အလယ်တန်း ၀.၀၈–၀.၁၆s သာ ⇒ စာသားက
 #    **စကားပြောနေတုန်း** ပေါ်သည် ⇒ `gfx_in_speech` မဖြစ်မနေ。
 # ⚠️ SFX အသိပ်သည်းမှုကို ၃ ပုဒ်လုံးမှ **မတိုင်းနိုင်ပါ** (တိတ်ဆိတ်မှု
 #    ကွက်လပ် မရှိ၍ detector ရှာစရာ မရှိ) ⇒ house တန်ဖိုး သုံးသည်。

 # ① ref1 — talking head · အောက်တန်း စာတန်း အခြေခံ
 #    စာသား ၃၅% (အောက် ၄၁% ⇒ caption ၀.၁၄ · ဂရပ်ဖစ် ၀.၂၁) ·
 #    ဖြတ်ချက် ၈.၁/မိနစ် · shot အလယ် ၂.၈၃s
 #    ⇒ ကတ် ၃၄ ခု/၅ မိနစ် (၆.၅/မိနစ်) — **ရနိုင်သည်**。
 "ref-talk": dict( gfx_gap_max=6.0,
    # ⚠️ Fast Cut ကို ဤပုံစံထဲ ပေါင်းထားသည် (Zin ၂၀၂၆-၀၉-၂၀)。
    #    `pace="fast"` ရွေးလျှင် ဖြတ်ချက် ၂၈/မိနစ် ပုံစံ ရမည်。
    pace="normal",
    # ⚠️ **High-Retention Talking-Head** (Zin ၂၀၂၆-၀၉-၂၀ · ref `KCN4-2hyUBM`
    #    နှင့် `01BnhfTaQoo` — creator တူ)。 တိုင်းချက်: စာသား ၄၆%၊ အောက်ပိုင်း
    #    ၁၄% ⇒ **burned-in စာတန်း မသုံး**。 keyword pop နဲ့ ဘောင်အပြည့် ကတ်သာ。
    #    accent #E5BC32 (frame ၃ ခုမှ တိုင်း — ZJL ရဲ့ #FFE000 နဲ့ RGB ၁၁၂ ကွာ)。
    # ⚠️ accent ကို **IKKI brand** သို့ ပြောင်းထားသည် (Zin ၂၀၂၆-၀၉-၂၀:
    #    「Ikki Brand Color themes ကိုသုံးပေးပါ」 → 「အရောင်အသစ် သတ်မှတ်ပါ」)。
    #    ⚠️ အရင်က #FFE000 (app.css ရဲ့ --ac) သုံးခဲ့ရာ **ZJL နဲ့ တစ်ထပ်တည်း**
    #    ဖြစ်နေသည် ⇒ IKKI ကိုယ်ပိုင် အအေးရောင် သတ်မှတ်ထားသည်。 တိုင်းချက်:
    #    ⚠️ ငါ ဖျော့စိမ်း #22D3C5 ကို တိုင်းပြီး ရွေးခဲ့ရာ Zin က
    #    **အဝါပဲ ဆက်သုံး**ဟု ဆုံးဖြတ်သည် (၂၀၂၆-၀၉-၂၁)。 တိုင်းချက်က
    #    「ဘယ်အရောင် ဖတ်ရလွယ်လဲ」ကို ဖြေပေးသည်、「brand ဘာလဲ」ကို မဖြေပါ —
    #    ဒါက ပိုင်ရှင်ရဲ့ ဆုံးဖြတ်ချက် ဖြစ်သည်。
    #    ⚠️ ZJL ရဲ့ GOLD နဲ့ တူညီသည် — ကွဲပြားမှုက နောက်ခံ (#0A0A0A vs
    #       #101014) နဲ့ ဖောင့် (MasterpieceUniRound vs MyanmarYinmar)。
    # Talking Head ကလည်း Headtop နည်းတူ plan-driven ဖြစ်ရမည်။ အရင်က ဒီ style
    # တစ်ခုတည်းက generic renderer လမ်းကြောင်းကနေ ထွက်ခဲ့၍ AI plan ရဲ့
    # template / semantic SFX / punch-in မည်သည့်အရာမှ final render မရောက်ခဲ့။
    # `plan` ဟာ UI မှာ edit plan ပြရန်လည်း အခြေခံဖြစ်သည်။
    plan=True, energy="standard", motion="normal", broll_freq="normal",
    sfx_on=True, autocut=True, shot_grade=True, motionkit_profile="premium",
    # အကြောင်းအရာနဲ့ မချိတ်ထားသော stock ကို budget ပြည့်စေရန် မထည့်ရ။
    # Premium talking-head မှာ B-roll နည်းနည်းနည်းသော်လည်း မှန်ရမည်။
    broll_strict=True,
    cap_typo=0.22, accent="#22D3C5", insert_per_min=2.5, zoom_amt=0.055,
     label="Talking Head Motion Edit", theme="ikki", fps=30,
     keep_pause=0.20, min_sil=0.32,
     # ⚠️ **reference ဖိုင်ကိုယ်တိုင် frame ၁၉၆ ခု တိုင်းထားသည်**
     #    (KCN4-2hyUBM 1080p · ၂၀၂၆-၀၉-၂၀)。 အရင်က JSON calib ရဲ့
     #    ပျမ်းမျှနဲ့ ချထားရာ Zin က 「၃/၁၀ · premium မဆန်」ဟု ပြောခဲ့သည်。
     #    စာလုံး အမြင့် — reference အလယ်တန်း ၃.၆% ·H · p75 **၅.၇%**
     #    (ငါတို့ ၂.၆% က reference ရဲ့ **p25** မှာ ကပ်နေသည် = အငယ်ဆုံး)。
     #    စာတန်း ပေါ်ချိန် — reference **၇၂%** frame (ငါတို့ ၁၄%)。
     #    နေရာ — အလယ် y **၇၂%** (ငါတို့ ၇၈%)。
     captions="accent", cap_pct=0.050, cap_base=0.72, cap_max=0.87,
     cap_cover=0.70,
     gfx=16, gfx_share=(0.17, 0.25),
     gfx_in_speech=True, gfx_min_sil=0.30,
     broll=6, broll_pct=0.18, broll_max=3.0,
     slides=False,
     sfx_per_min=1.5,
     music="calm", mmf="MasterpieceUniRound", latin="Figtree-Black",
     natural=True,   # သဘာဝ grade (၂၀၂၆-၀၉-၂၀)
     lufs=-14.0, sat=1.06, vign=0.6, scrim=False,
 ),

 # ② ref2 — ဂရပ်ဖစ် ထူ · ဘောင်အပြည့် ကတ်
 #    စာသား ၈၂% · အလယ် ၇၇% · ဧရိယာ အများဆုံး ၇၉.၆% ⇒ **full-frame slide**
 #    ⚠️ ကတ်နဲ့ဆို ၂၁၅ ခု လိုမည် — **မရနိုင်**。 ⇒ slide က အဓိက ထမ်းသည်
 #      (slide တစ်ခု ၁၇s အထိ ဆန့်၍ share မြင့်နိုင်)。
 "ref-slides": dict(
     label="Slide Heavy", theme="zjl", fps=30,
     keep_pause=0.22, min_sil=0.35,
     captions="accent", cap_pct=0.024, cap_base=0.78, cap_max=0.87,
     cap_cover=0.08,
     gfx=14, gfx_share=(0.30, 0.42),
     gfx_in_speech=True, gfx_min_sil=0.30,
     # ⚠️ ၁၇.၀ က reference ရဲ့ **တိုင်းချက်** — ဒါပေမယ့် QC ရဲ့ `CARD_MAX`
     #    ၁၀.၅ ကို မကျော်ရ (worker က `min()` နဲ့ ချုပ်ထားသည်) ⇒ တကယ် သုံးတာ
     #    **၁၀.၅**。 ဂိတ်ကိုယ်တိုင် တင်ချင်လျှင် `core/qc.py` မှာ Zin
     #    အတည်ပြုမှ ပြင်ရမည် ("ဂိတ် မလျှော့ရ")。 slide ကို ပိုများအောင်
     #    ထုတ်ပြီး `gfx_share` ဘောင် အလယ် ၀.၃၆ ကို ရနေသဖြင့် ယခု မလိုပါ。
     card_max_s=17.0,
     broll=4, broll_pct=0.14, broll_max=3.0,
     slides=True,
     sfx_per_min=0.9,
     music="calm", mmf="MasterpieceUniRound", latin="Figtree-Black",
     natural=True,   # သဘာဝ grade (၂၀၂၆-၀၉-၂၀)
     lufs=-14.0, sat=1.05, vign=0.6, scrim=False,
 ),

 # ③ ref3 — အလွန်မြန် ဖြတ်ချက် · အပေါ်ပိုင်း သုံးမှု မြင့်
 #    ဖြတ်ချက် **၂၇.၉/မိနစ်** (ref1/ref2 ရဲ့ ၃.၅ ဆ) · shot အလယ် ၁.၂၇s ·
 #    ၆၄% က ၂s အောက် · စာသား ၄၆% (အပေါ် ၃၄% · အောက် ၁၄% သာ)
 #    ⚠️ ကတ်နဲ့ဆို ၁၆၃ ခု လိုမည် — **မရနိုင်**。 ⇒ ဤ style ရဲ့ လက္ခဏာက
 #      **ဖြတ်ချက် တင်းမှု** ဖြစ်သည် ⇒ `keep_pause`/`min_sil` ကို တင်းထားသည်。
# ⚠️ **Talking Head Motion Edit** — Zin ရဲ့ ၂၀၂၆-၀၉-၂၀ spec。
#    UI မှာ ယခင် `Headtop` + `Talking Head Motion Edit` ကို တစ်မျိုးတည်း
#    ပေါင်းထားသော canonical recipe ဖြစ်သည်။ plan ကို အကောင်အထည်ဖော်၍ event
#    တိုင်း သုံးစွဲသူ ပြင်နိုင်သည်။ `ref-talk` ကို အဟောင်း jobs မပျက်စေရန်သာ
#    R ထဲထားပြီး UI ကနေ ဖျောက်ထားသည်。
# ⚠️ စာတန်း ကိန်းများကို reference (KCN4-2hyUBM) ကနေ တိုင်းယူထားသည် —
#    ပေါ်ချိန် ၇၂% · အမြင့် အလယ်တန်း ၃.၆%·H (p75 ၅.၇%) · အလယ် y ၇၂%。
#    ⚠️ `cap_base` ကို **အောက်ခြေမှ ၇–၉%** ဟု spec မှာ သတ်မှတ်ထားသဖြင့်
#       ၀.၉၂ (= အောက်ခြေမှ ၈%) ထားသည် — QC `cap_max` ၀.၉၃ အောက်。
 "headtop": dict( gfx_gap_max=6.0,
     label="Talking Head Motion Edit", theme="ikki", fps=30,
     plan=True, energy="standard", shot_grade=True,
     motionkit_profile="premium", broll_strict=True,
     keep_pause=0.20, min_sil=0.32,
     captions="accent", cap_pct=0.050, cap_base=0.92, cap_max=0.93,
     cap_cover=0.85, cap_typo=0.0,
     mmf="MasterpieceUniRound", latin="Figtree-Black",
     accent="#FFE000", stroke="#0A0A0A", stroke_w=0.06,
     gfx=16, gfx_share=(0.17, 0.25), broll=6, broll_pct=0.18,
     music="calm", lufs=-14.0, sfx_per_min=1.5,
     # ⚠️ `motion` · `broll_freq` ကို **အတိအလင်း ပေးရမည်** — None ဆိုလျှင်
     #    UI မှာ 「မရွေးရသေး」ဖြစ်ပြီး သုံးစွဲသူက ဘာ သက်ရောက်နေလဲ မသိပါ。
     motion="normal", broll_freq="normal",
     zoom_amt=0.045, natural=True, grade=True,
     sat=1.03, vign=0.0, cbal=False),

 "ref-fast": dict(
     label="Fast Cut", theme="zjl", fps=30,
     keep_pause=0.12, min_sil=0.22,
     captions="accent", cap_pct=0.026, cap_base=0.78, cap_max=0.87,
     cap_cover=0.12,
     gfx=20, gfx_share=(0.20, 0.30),
     gfx_in_speech=True, gfx_min_sil=0.22,
     broll=8, broll_pct=0.20, broll_max=2.5,
     slides=False,
     sfx_per_min=1.2,
     music="calm", mmf="MasterpieceUniRound", latin="Figtree-Black",
     natural=True,   # သဘာဝ grade (၂၀၂၆-၀၉-၂၀)
     lufs=-14.0, sat=1.10, vign=0.6, scrim=False,
 ),

 "knowledge": dict(
    # ⚠️ Slide Heavy ကို ဤပုံစံထဲ ပေါင်းထားသည် (Zin ၂၀၂၆-၀၉-၂၀)。
    #    `slide_amt="heavy"` ရွေးလျှင် ဘောင်အပြည့် ကတ် အဓိက ပုံစံ ရမည်。
    slide_amt="light",
    # ⚠️ **High-Retention Talking-Head** (Zin ၂၀၂၆-၀၉-၂၀ · ref `KCN4-2hyUBM`
    #    နှင့် `01BnhfTaQoo` — creator တူ)。 တိုင်းချက်: စာသား ၄၆%၊ အောက်ပိုင်း
    #    ၁၄% ⇒ **burned-in စာတန်း မသုံး**。 keyword pop နဲ့ ဘောင်အပြည့် ကတ်သာ。
    #    accent #E5BC32 (frame ၃ ခုမှ တိုင်း — ZJL ရဲ့ #FFE000 နဲ့ RGB ၁၁၂ ကွာ)。
    cap_typo=0.22, accent="#E5BC32", insert_per_min=2.5,
    # ⚠️ REF-A 14.0% · REF-B 13.4% (တိုင်းထားသည်) — skill P1
    gfx_share=(0.10, 0.17), label="Knowledge Sharing", theme="zjl", fps=30,
    keep_pause=0.26, min_sil=0.45, captions="accent", gfx=10, music="calm",
    mmf="MasterpieceUniRound", latin="Figtree-Black",
    #    ⚠️ ဒုတိယအကြိမ် တိုင်းချက် (frame ၃၀၀) — ဖွဲ့စည်းပုံ:
    #         ပြောသူ      ၈၃% / ၈၀%
    #         full-screen slide  ၁၃% / ၈%
    #         ရုပ်ကြမ်း   **၃% / ၁၂%** ← ZAE ရဲ့ ၆၂% နှင့် လုံးဝ ဆန့်ကျင်
    #    ⇒ Knowledge Sharing က **ပြောသူ ဗီဒီယို**。 ရုပ်ကြမ်း အနည်းငယ်သာ
    #      ဖောက်ထည့်သည်。 ZAE ပုံစံ (ရုပ်ကြမ်းများများ) ကို ဒီမှာ မသုံးရ。
    #    ⚠️ အလေးပေး အရောင်ကို **မယူပါ** — Zin ညွှန်ကြားချက် (ကိုယ်ပိုင်
    #       ဘရန်း အရောင် သုံးရမည်)。
    cap_pct=0.024, cap_base=0.780, lufs=-14.0, cap_max=0.870, scrim=False,
    broll=4, broll_pct=0.18, broll_max=3.0, cap_cover=0.15,
    # ⚠️ **full-frame slide** — ဒီပုံစံရဲ့ အဓိက ဂရပ်ဖစ်。 reference (၉:၁၅) မှာ
    #    slide ၁၂ ခု · ၇၄.၅s = ၁၃.၄% (တိုင်းထားသည်)。 lower-third အသေးလေးနဲ့
    #    ၂.၅% ပဲ ရပြီး "မမိုက်ဘူး" ဖြစ်ခဲ့သည် — အရေအတွက် မဟုတ်、**အရွယ်** က အရေးကြီး。
    slides=True,
    natural=True,   # သဘာဝ grade (၂၀၂၆-၀၉-၂၀)
    sat=1.05, vign=0.60, sfx_per_min=0.9),
 # ── Short Video = **ZAE style** ──
 #    reference ဗီဒီယို ၂ ခု (58s · 86s) မှ **တိုင်းယူထားသော** ကိန်းများ:
 #    3:4 · 30fps · စာတန်း 8% of H · baseline 81% · navy stroke #1E3B5A ·
 #    −17.7 LUFS (feed video မို့ ZJL ထက် တိတ်သည်)
 # ⚠️ ဤကိန်းများကို **ZAE_N5_ONLINE project ရဲ့ မှတ်တမ်းမှ** ယူထားသည် —
 #    မှန်းချက် မဟုတ်、Zin ကိုယ်တိုင် အတည်ပြုထားသော ကိန်းများ:
 #      ဖောင့်      MyanmarHeadOne (Pyidaungsu-Bold မဟုတ်)
 #      အရွယ်      H×0.0535 — Zin "Font size နည်းနည်းကြီးနေသလို" ⇒
 #                  0.0605 (87px) မှ 0.0535 (77px) သို့ လျှော့ခဲ့သည်
 #      အောက်ခြေ   H×0.845 (reference 83.4%)
 #      သီချင်း    သူ့ကိုယ်ပိုင် bed · **ducking မလုပ်**
 #      LUFS       −18.8 (တိုင်းထားသည်)
 "short-video": dict(label="Short Video · ZAE", theme="zae", fps=30,
    # ⚠️ reference မှာ ဂရပ်ဖစ် ကတ်ကြီး **မရှိသလောက်** — စာတန်းနဲ့ B-roll ချည်းပဲ。
    keep_pause=0.18, min_sil=0.34, captions="zae", gfx=2, music="zae",
    mmf="MyanmarHeadOne", latin="Figtree-Black",
    # ⚠️ Zin ရွေးချယ်ချက် (၂၀၂၆-၀၉-၁၃) — နမူနာ ၄ မျိုး (77/93/115/136px)
    #    ကို မြင်ပြီး **136px = 0.095** ကို ရွေးသည်。 N5 project ရဲ့ 0.0535
    #    က ကိန်းအရ ကိုက်ပေမယ့် သူ မြင်ရတာ သေးလွန်းသည် — အမြင်က ကိန်းထက်
    #    အထက်တန်း。
    # ⚠️ စာတန်း ၃၀% ကို typography template နဲ့ ထုတ်သည် — ကျန်တာ
    #    ပုံမှန်。 အားလုံး typography လုပ်လျှင် ဖတ်ရ ပင်ပန်းပြီး
    #    အလေးထားချက် ပျောက်သည်。
    cap_typo=0.30,
    # ⚠️⚠️ **၂၀၂၆-၀၉-၂၀ — Zin ရဲ့ ၂၀၂၆-၀၉-၁၃ ရွေးချယ်ချက်ကို ပြန်ပြင်ထားသည်**。
    #    အထက်က မှတ်ချက်အတိုင်း သူက ၀.၀၉၅ ကို မျက်စိနဲ့ ရွေးပြီး ၀.၀၅၃၅ ကို
    #    「သေးလွန်းတယ်」 ဟု ပယ်ခဲ့သည်。 ဒါပေမယ့် ၂၀၂၆-၀၉-၂၀ မှာ သူကိုယ်တိုင်
    #    reference (`1.mp4`) ပေးပြီး 「ဒီပုံစံအတိုင်း အတိအကျ」 ဟု ပြောသည်。
    #    တိုင်းချက် — reference ရဲ့ စာတန်း မှင်အမြင့် ဘောင်၏ **၇.၄၅%**
    #    (2880px ဘောင်မှာ 214px · တစ်ကြောင်းတည်း frame ၁၉၄ ခု အလယ်တန်း)。
    #    မှင်/em အချိုး ၁.၇၂–၁.၉၉ (cttext နဲ့ တိုင်းထား) ⇒ **em ၀.၀၄၃**。
    #    ယခင် ၀.၁၀၀ က မှင် ၁၉.၁% ⇒ reference ထက် **၂.၆ ဆ ကြီး**ခဲ့သည်。
    #    ⇒ မကြိုက်လျှင် ဤတစ်ကြောင်းကို `cap_pct=0.100` ပြန်ထားရုံ。
    # ⚠️ `stroke="brand"` — ကိန်းသေ မဟုတ်တော့ဘဲ **brand ရဲ့ အရောင်** ကို
    #    ယူသည် (Zin: 「အခြား brand က logo နဲ့ color ရွေးလိုက်တာနဲ့ အဲဒီ
    #    theme အတိုင်း」)。 reference ရဲ့ အနားသတ်က navy #1A3856 —
    #    ZAE ရဲ့ #1E3B5A နဲ့ နီးပါး တူသဖြင့် ZAE မှာ အပြောင်းအလဲ မရှိသလောက်。
    cap_pct=0.043, cap_base=0.877, stroke="brand", stroke_w=0.16,
    # ⚠️ reference မှာ စာတန်းက frame ရဲ့ **၉၃%** မှာ ပါသည် (292 ခုမှ 273)。
    cap_cover=0.93,
    # ⚠️ −18.8 က N5 reference ကနေ တိုင်းယူထားတာ — ဒါပေမယ့် **reference
    #    ကိုယ်တိုင်က တိုးလွန်း**သည် (skill `ikki-presentation` §8: REF-B
    #    −22.58 ကို "၈ dB အောက်" ဟု ဆိုထားသည်)。 platform တွေက ~−14 ကို
    #    normalise လုပ်သဖြင့် feed ထဲမှာ တခြားဟာတွေထက် တိုးနေမည်。
    #    ⇒ **ဖွဲ့စည်းပုံကို လိုက် · mastering ကို ပြင်**。 လိုလျှင် style editor
    #      ကနေ −17.7 ပြန်ရွေးလို့ ရသည်。
    # ⚠️ reference တိုင်းချက် — B-roll **၃၃%** (studio မဟုတ်သော frame)。
    #    ယခင် ၀.၅၁ က များလွန်းသည်。
    lufs=-14.5, cap_max=0.870, cap_wide=0.63, sfx=False, scrim=True, broll=10, broll_pct=0.33, broll_max=4.5,
    sat=1.00, vign=0.0, cbal=False, sfx_per_min=0.9,
    # ⚠️ imin ၀.၁၀ က **အရိပ်ကို ချေမှုန်း**သည် — tokutei (ZAE source အစစ်) မှာ
    #    မူရင်း ၀.၀၄% ⇒ ၁.၂၆% · p05 ၅၂ ⇒ ၂၉ (၂၀၂၆-၀၉-၂၀ တိုင်း၍ တွေ့)。
    #    sweep: .10→၁.၂၆% · .06→၀.၃၀% · .04→၀.၁၉% · **.03→၀.၁၃%**。
    #    အလယ်တန်း ၂၄၇ မပြောင်း — contrast က အဖြူနံရံကနေ ရနေပြီးသား。
    lv_imin=0.03, lv_imax=1.0, lv_omin=0.02, curve="none"),
    # ⚠️ B-roll ၆၂% — N5 ONLINE reference ကနေ **တိုင်းယူထားသည်**
    #    (frame ၆၀ ကနေ: အဖြူနံရံ ပြောသူ ၃၈% · ရုပ်ကြမ်း ၆၂%)。
    #    ၃၀% ပုံသေ ထားတုန်းက ရုပ်ကြမ်း ၅.၅% ပဲ ထွက်ခဲ့ပြီး reference နှင့်
    #    လုံးဝ မတူခဲ့。 ဒါက ဒီပုံစံရဲ့ **အဓိက ကွာဟချက်** ဖြစ်သည်。
    # ⚠️ ZAE spec: B-roll **၂၂–၃၂%** — ၆၀s မှာ ~၆ ခု (တိုင်းထားသည်)
 "promotional": dict(label="Promotional", theme="zae", fps=30,
    keep_pause=0.22, min_sil=0.40, captions="big", gfx=8, music="corporate",
    mmf="NotoSansMyanmar", latin="Manrope",
    cap_pct=0.0481, cap_base=0.680, cap_cover=0.45, lufs=-13.5, broll=0,
    sat=1.00, vign=0.0, cbal=False, sfx_per_min=1.2,
    # ⚠️ imin ၀.၁၀ က **အရိပ်ကို ချေမှုန်း**သည် — tokutei (ZAE source အစစ်) မှာ
    #    မူရင်း ၀.၀၄% ⇒ ၁.၂၆% · p05 ၅၂ ⇒ ၂၉ (၂၀၂၆-၀၉-၂၀ တိုင်း၍ တွေ့)。
    #    sweep: .10→၁.၂၆% · .06→၀.၃၀% · .04→၀.၁၉% · **.03→၀.၁၃%**。
    #    အလယ်တန်း ၂၄၇ မပြောင်း — contrast က အဖြူနံရံကနေ ရနေပြီးသား。
    lv_imin=0.03, lv_imax=1.0, lv_omin=0.02, curve="none"),
 "brand-review": dict(label="Brand Review", theme="zjl", fps=30,
    keep_pause=0.40, min_sil=0.75, captions="plain", gfx=9, music="calm",
    mmf="Padauk", latin="Manrope",
    cap_pct=0.0481, cap_base=0.680, cap_cover=0.80, lufs=-14.5, broll=0,
    natural=True,   # သဘာဝ grade (၂၀၂၆-၀၉-၂၀)
    sat=1.00, vign=0.50, cbal=False, sfx_per_min=0.8),
 "short-biz": dict(label="Short Video", theme="zae", fps=30,
    keep_pause=0.20, min_sil=0.38, captions="big", gfx=6, music="corporate",
    mmf="NotoSansMyanmar-Bold", latin="ArchivoBlack",
    cap_pct=0.0333, cap_base=0.620, lufs=-13.5, broll=0,
    sat=1.00, vign=0.0, cbal=False, sfx_per_min=1.1,
    # ⚠️ imin ၀.၁၀ က **အရိပ်ကို ချေမှုန်း**သည် — tokutei (ZAE source အစစ်) မှာ
    #    မူရင်း ၀.၀၄% ⇒ ၁.၂၆% · p05 ၅၂ ⇒ ၂၉ (၂၀၂၆-၀၉-၂၀ တိုင်း၍ တွေ့)。
    #    sweep: .10→၁.၂၆% · .06→၀.၃၀% · .04→၀.၁၉% · **.03→၀.၁၃%**。
    #    အလယ်တန်း ၂၄၇ မပြောင်း — contrast က အဖြူနံရံကနေ ရနေပြီးသား。
    lv_imin=0.03, lv_imax=1.0, lv_omin=0.02, curve="none"),
 # ⚠️ Course — ဖြတ်တောက် **လုံးဝ မလုပ်ရ**
 "course": dict(label="Course", theme="zjl", fps=30,
    keep_pause=None, min_sil=None, captions="plain", gfx=10, music=None,
    mmf="PadaukBook-Bold", latin="Figtree",
    cap_pct=0.0426, cap_base=0.880, lufs=-14.5, broll=0,
    natural=True,   # သဘာဝ grade (၂၀၂၆-၀၉-၂၀)
    sat=1.02, vign=0.25, sfx_per_min=0.5),
}
DEF = dict(
    # ⚠️ **စည်းချက် — ဂရပ်ဖစ် ကွက်လပ် အမြင့်ဆုံး (s)**。 reference ၆ ပုဒ်
    #    တိုင်းရာ မြင်ကွင်း ပြောင်းလဲမှု ၉.၃–၁၄.၃/min ⇒ အကွာ ၄.၂–၆.၅s。
    #    label classifier က ၂၃% သာ ထုတ်သဖြင့် ကွက်လပ် ရှည်လျှင်
    #    ဖြည့်ရသည် (pattern interrupt)。 ၀ = မဖြည့်。
    gfx_gap_max=0.0,
    # ⚠️ **ပုံသေ ပိတ်** — ချောင်းဆိုးသံ/ဖြည့်စကားကို ညွှန်ပြရုံ。
    #    `coughs()` က အမြင့်ဘန်း တက်မှုကိုသာ ရှာ၍ စ/ဆ သံ · ကီးဘုတ်နဲ့
    #    မခွဲနိုင်ပါ — precision မတိုင်းရသေး。 benchmark အောင်မှ ဖွင့်ရမည်。
    auto_clean=False,cap_pct=None, cap_base=None, stroke=None, stroke_w=0.0,
           cap_cover=None, cap_accent=None, broll_pct=0.30, broll_max=3.2,
           sfx=True, cap_typo=0.0, sat=None, vign=None, cbal=True, grade=True,
           # ⚠️ ဖြတ်ဆက်ကို ဖုံးရန် punch-in (၁.၀ = ပိတ်)。 `spans.PUNCH` က ပုံသေ。
           #    Course က ဖြတ်တောက် မလုပ်သဖြင့် အလိုအလျောက် သက်ရောက်မှု မရှိ。
           punch=None,
           # ⚠️ theme ရဲ့ GOLD ကို လွှမ်းရန် (High-Retention style) — မရှိလျှင် theme အတိုင်း
           accent=None, slide_src=None,
           # ⚠️ explainer insert နှုန်း (/မိနစ်) — reference ၂.၅
           insert_per_min=None,
           # ပေါင်းထားသော ပုံစံ ရွေးချက်
           slide_amt=None, pace=None,
           # ⚠️ ရုပ်ကို တဖြည်းဖြည်း ချုံ့/ချဲ့ခြင်း — ၀ = မလုပ်。
           #    အတိမ်အနက်ကို reference ကနေ **မတိုင်းရသေးပါ**、ဘောင်အတွင်း
           #    (≤၁.၂၅×) ဒီဇိုင်း ရွေးချယ်မှု ဖြစ်သည်。
           zoom_amt=0.0,
           # ── plan-driven Talking Head / Headtop ထိန်းချုပ်ချက် ──
           # ⚠️ `plan=True` ဆိုမှ plan လမ်းကြောင်း သုံးသည် ⇒ ကျန် ပုံစံ ၁၀ ခု
           #    ယခင်အတိုင်း — worker က ဆုံးဖြတ်နေဆဲ。 တစ်ပြိုင်နက် မပြောင်းရ。
           plan=False,              # plan-driven render သုံးမလား
           # MotionKit ထဲက template အားလုံးကို raw ID နဲ့ မပေးရ။ shot-safe-zone,
           # required props နဲ့ renderer support ကို စစ်ပြီးသော profile ပဲ ရွေးစေသည်။
           motionkit_profile="premium",
           energy=None,             # minimal · standard · dynamic
           broll_freq=None,         # B-roll ဘယ်လောက် မကြာခဏ
           motion=None,             # ရုပ် လှုပ်ရှားမှု ပြင်းအား
           sfx_on=True,
           autocut=True,            # တိတ်ဆိတ်မှု အလိုအလျောက် ဖြတ်
           review=True,             # render မလုပ်ခင် transcript ပြ
           shot_grade=False,        # အပိုင်းလိုက် grade (အပြင်/အတွင်း)
           # ⚠️ ကိန်းသေ **မထားရ** — `min_sil` က ပုံစံတိုင်း သီးသန့် တိုင်းထားသည်
           #    (cinematic-vlog ၁.၂၀ · ref-fast ၀.၂၂ · course မဖြတ်)。 ဒီမှာ
           #    ၄၀၀ ဟု ထားလျှင် `_expand()` က အားလုံးကို ၀.၄၀ သို့ ပြားစေခဲ့သည်
           #    (၂၀၂၆-၀၉-၂၁ ကိုယ်တိုင် ထည့်မိပြီး ဖမ်းမိသည်)。
           #    ⇒ **ပြသရန်သာ** — `_expand()` က `min_sil` ကနေ တွက်ပေးသည်。
           silence_ms=None,         # တိတ်ဆိတ်မှု ဖြတ်မှတ် (ms) — ဆင်းသက်ချက်
           broll_gap=3.0, sfx_per_min=None, cap_hold=4.0, broll_minscore=2.0,
           broll_tail=5.0, cap_gap=0.18, cap_fade=0.14, cap_wide=0.86,
           gfx_share=None,
           lv_imin=None, lv_imax=None, lv_omin=None, lv_omax=None, curve=None,
           cap_fill=None, cap_stroke=None,
           lufs=-14.0, cap_max=None, scrim=False, broll=0)

# ⚠️ **ပေါင်းထားသော ပုံစံများ** (၂၀၂၆-၀၉-၂၀ · Zin)。
#    `ref-slides` → Knowledge Sharing ရဲ့ slide "ထူထူ"
#    `ref-fast`   → Talking Head Motion Edit ရဲ့ pace "မြန်"
#    `ref-talk`   → Talking Head Motion Edit နဲ့ UI ပေါ်မှာ ပေါင်းပြီးသား
#    ⚠️ အဟောင်း ၃ ခုကို **R ထဲ ချန်ထားရမည်** — ရှိပြီးသား job တွေရဲ့
#       `recipe` ကော်လံမှာ အဲဒီနာမည် ရေးထားပြီး၊ ဖျက်လျှင် `get()` က
#       `cinematic-vlog` သို့ ပြန်ဆုတ်ကာ **ပုံစံ တိတ်တဆိတ် ပြောင်း**မည်。
#       ⇒ `_hidden` နဲ့ UI ကနေသာ ဖယ်သည်。
HIDDEN = {"ref-talk", "ref-slides", "ref-fast"}

# slide ပမာဏ — Knowledge Sharing
# ⚠️ `card_max_s` ကို **ဖယ်ထားသည်**。 ဂိတ်ဆီ မရောက်ဘဲ (run.py:1609 က `pass`)
#    renderer ကလည်း `min(…, QC.CARD_MAX)` နဲ့ ၁၀.၅s ချထားသဖြင့် ဘာမှ မလုပ်ပါ。
# ⚠️ ကတ် အရှည် ၁၀.၅s ကန့်သတ်ဖြစ်၍ **ဖုံးအုပ်မှုက အရေအတွက်နဲ့ပဲ ရသည်**:
#    `gfx × 10.5 ÷ dur ≥ 0.30` လိုသည်。 ၁၄ ခုဆိုလျှင် ၅၅၅s မှာ ၀.၂၆၅ ပဲ ရကာ
#    QC ကျသည် (တကယ် ဖြစ်ခဲ့သည်)。 ၉၀၀s အထိ မီစေရန် ၃၀ ထားသည်
#    (၃၀ × ၁၀.၅ ÷ ၉၀၀ = ၀.၃၅)。 ⇒ ဂိတ် မလျှော့ဘဲ ယန္တရား ချဲ့ထားသည်。
SLIDE_AMT = {
    "light": dict(gfx_share=(0.10, 0.17), gfx=10),
    "heavy": dict(gfx_share=(0.30, 0.42), gfx=30),
}
# ဖြတ်ချက် အမြန်နှုန်း — Talking Head Motion Edit
# ⚠️ `sfx_per_min` ကို **ဂိတ်ရဲ့ အမြင့်ဆုံး (၁.၅)** အထိ တင်ထားသည်。
#    reference (KCN4-2hyUBM) မှာ မြင်ကွင်းပြောင်းချိန်နဲ့ တိုက်ဆိုင်သော
#    အသံ ၉၂ ခု = **၇/မိနစ်** ရှိသည် — ငါတို့ ဂိတ်က ၁.၅ ⇒ ၅ ဆ နည်းသည်。
#    ⚠️ **ဂိတ်ကို မထိပါ** (「ဂိတ် မလျှော့ရ」) — ဂိတ်ကိုယ်တိုင် တင်ဖို့က
#    Zin ရဲ့ အတည်ပြုချက် လိုသည် (`core/qc.py` ရဲ့ sfx_density)。
PACE = {
    "normal": dict(keep_pause=0.20, min_sil=0.32, gfx=16, gfx_share=(0.17, 0.25),
                   broll=6, sfx_per_min=1.5),
    "fast":   dict(keep_pause=0.12, min_sil=0.22, gfx=20, gfx_share=(0.20, 0.30),
                   broll=8, sfx_per_min=1.5),
}


def _expand(r):
    """`slide_amt` / `pace` ရွေးချက်ကို ကိန်းများအဖြစ် ဖြန့်သည်。

    ⚠️ **`apply()` အဆုံးမှာပါ ပြန်ခေါ်ရမည်**。 `get()` ထဲမှာပဲ ဖြန့်လျှင်
       `apply()` က သုံးစွဲသူ ပြင်ချက်ကို **နောက်မှ** ပေါင်းသဖြင့်
       `slide_amt="heavy"` ရွေးလည်း ကိန်းတွေ မပြောင်းပါ (၂၀၂၆-၀၉-၂၀ တကယ် ဖြစ်)。
       `natural` မှာလည်း ဒီအမှားမျိုး ဖြစ်ခဲ့ဖူးသည် — အလွှာ အစဉ် အရေးကြီးသည်。
    """
    sa = SLIDE_AMT.get(r.get("slide_amt") or "")
    if sa: r.update({k: v for k, v in sa.items() if v is not None})
    pc = PACE.get(r.get("pace") or "")
    if pc: r.update(pc)

    # ══ Headtop ထိန်းချုပ်ချက် → တကယ့် ကိန်းများ ════════════════
    # ⚠️ ၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့ — `motion` · `broll_freq` · `sfx_on` ·
    #    `autocut` · `silence_ms` တို့က `BOUNDS` မှာ စစ်ပြီး DB မှာ သိမ်းပေမယ့်
    #    **worker က ဘယ်မှာမှ မဖတ်ခဲ့ပါ** ⇒ ခလုတ်တွေက ဘာမှ မလုပ်ခဲ့ပါ。
    #    ⇒ ဒီမှာ ရှိပြီးသား ကိန်းတွေအဖြစ် ဖြန့်သည် — worker ကို မထိရပါ。
    # ⚠️ **`_expand()` ထဲမှာ ဖြစ်ရမည်** — `apply()` က သုံးစွဲသူ ပြင်ချက်ကို
    #    နောက်မှ ပေါင်းသဖြင့် အပေါ်က `slide_amt` အမှားမျိုး ထပ်ဖြစ်မည်。

    # တိတ်ဆိတ်မှု ဖြတ်မှတ် — `min_sil` (စက္ကန့်) က **တစ်ခုတည်းသော အမှန်**、
    # `silence_ms` က UI အတွက် ပြသချက်သာ ⇒ **တစ်လမ်းသွား**。
    # ⚠️ နှစ်လမ်းသွား လုပ်လျှင် DEF ရဲ့ ကိန်းက ပုံစံတိုင်းရဲ့ တိုင်းချက်ကို
    #    လွှမ်းမိမည် (အထက်က မှတ်ချက် ကြည့်)。 သုံးစွဲသူ ပြင်ချက်ကို
    #    `apply()` က `min_sil` အဖြစ် **အရင် ပြောင်း**ပေးသည်。
    r["silence_ms"] = (int(round(float(r["min_sil"]) * 1000))
                       if r.get("min_sil") is not None else None)

    # ဖြတ်တောက် ပိတ် — ရှိပြီးသား "မဖြတ်ပါ" လမ်းကြောင်းကိုပဲ သုံးသည်
    if r.get("autocut") is False:
        r["keep_pause"] = None

    # SFX ပိတ် — `sfx` က engine ဘက် အမည်
    if r.get("sfx_on") is False:
        r["sfx"] = False

    # B-roll မကြာခဏ — အရေအတွက်ကို အဆ လိုက်သည်
    _bf = {"low": 0.5, "normal": 1.0, "high": 1.5}.get(r.get("broll_freq") or "")
    if _bf is not None and r.get("broll"):
        r["broll"] = max(0, int(round(float(r["broll"]) * _bf)))

    # ရုပ် လှုပ်ရှားမှု — punch-in ပမာဏကို အဆ လိုက်သည်
    _mo = {"low": 0.5, "normal": 1.0, "high": 1.5}.get(r.get("motion") or "")
    if _mo is not None and r.get("zoom_amt"):
        # ⚠️ ဘောင် (BOUNDS zoom_amt ≤ ၀.၁၂) ကျော်၍ မရ — punch ၁.၀၈ ဆ
        #    ကန့်သတ်ချက်က မျက်နှာ မပျက်စေရန် တိုင်းထားသော ကိန်း。
        r["zoom_amt"] = round(min(0.12, float(r["zoom_amt"]) * _mo), 4)
    return r


def get(name):
    r = dict(DEF); r.update(R.get(name, R["cinematic-vlog"]))
    # ⚠️ `natural=True` ကို **ဒီမှာ** ဖြန့်ရသည် — `grade.chain()` ထဲမှာ ဖြန့်လျှင်
    #    သုံးစွဲသူရဲ့ sat/vign/lv_* ပြင်ချက်က `apply()` မှာ ပေါင်းပြီးသား ဖြစ်၍
    #    natural က ပြန်ဖျက်ပစ်မည် (slider သေမည်)。 recipe အလွှာမှာ ဖြန့်လျှင်
    #    သုံးစွဲသူ ပြင်ချက်က အပေါ်ကနေ ပြန်လွှမ်းနိုင်သည်。
    if name == "ref-slides": r["slide_amt"] = r.get("slide_amt") or "heavy"
    if name == "ref-fast":   r["pace"] = r.get("pace") or "fast"
    _expand(r)
    if r.get("natural"):
        # ⚠️ import ပုံစံ **နှစ်မျိုး** ရှိသည် — worker က `core/` ကို sys.path
        #    ထဲ ထည့်ပြီး `import recipes` (flat) လုပ်၊ API (Docker) က
        #    `from core import recipes` (package) လုပ်သည်。 တစ်မျိုးတည်း
        #    ရေးလျှင် တစ်ဖက်မှာ ကျသည် — ၂၀၂၆-၀၉-၂၀ မှာ worker က
        #    `ModuleNotFoundError: No module named 'core'` နဲ့ ရပ်သွားခဲ့သည်。
        r.update(NATURAL)
    return r


# ══ သုံးစွဲသူ ပြင်ချက် (override) ═══════════════════════════
# ⚠️ recipe ရဲ့ ကိန်းတွေက reference ဗီဒီယိုမှ **တိုင်းယူထားသည်**。
#    သုံးစွဲသူ ပြင်လို့ ရသင့်ပေမယ့် **ဘောင် မရှိဘဲ မရ** — cap_pct ၅၀%
#    ထည့်လိုက်လျှင် စာတန်းက frame တစ်ခုလုံး ဖုံးပြီး render က အလဟဿ ဖြစ်သည်。
#    ⇒ ဒီဇယားက ဘောင်。 API ရော worker ရော **တူတူ** ဒါကို သုံးရမည်。

# ဖြတ်မှု — (keep_pause, min_sil)。 အမည်ဖြင့် ရွေးရသည် —
# ⚠️ စက္ကန့် အစိတ်အပိုင်းကို သုံးစွဲသူ ကိုယ်တိုင် ထည့်ခိုင်းလျှင် အဓိပ္ပာယ်
#    မရှိ။ "၀.၁၈s" ဆိုတာ ဘာကို ဆိုလိုလဲ သုံးစွဲသူ မသိ。
CUTS = {
 "off":    (None,  None),   # လုံးဝ မဖြတ် — Course
 "gentle": (0.55, 1.20),    # Cinematic — အသက်ရှုသံ ချန်
 "normal": (0.40, 0.75),    # Vlog · Knowledge
 "tight":  (0.26, 0.45),    # Podcast
 "snappy": (0.18, 0.34),    # ZAE Short Video
}
CUT_LABEL = {
 "off":    ("မဖြတ်ပါ",      "No cutting"),
 "gentle": ("ညင်သာ",        "Gentle"),
 "normal": ("ပုံမှန်",       "Normal"),
 "tight":  ("တင်းတင်း",     "Tight"),
 "snappy": ("ပြတ်သား",      "Snappy"),
}
LUFS = {
 -13.5:  ("ကျယ် (−13.5)",            "Loud (−13.5)"),
 -14.0:  ("YouTube · Podcast (−14)", "YouTube · Podcast (−14)"),
 -14.5:  ("ပုံသေ (−14.5)",            "House default (−14.5)"),
 -16.0:  ("အလယ်အလတ် (−16)",          "Middle (−16)"),
 -17.7:  ("Feed · TikTok (−17.7)",   "Feed · TikTok (−17.7)"),
}
# ⚠️ စာတန်း အရွယ်ကို **အမည်နဲ့** ရွေးရသည် — "0.095" ဆိုတာ သုံးစွဲသူအတွက်
#    အဓိပ္ပာယ် မရှိ。 ကိန်းတွေက တိုင်းထားသော ဘောင်အတွင်း。
CAPSIZE = {
 # ⚠️ `xs` ကို ၂၀၂၆-၀၉-၂၀ မှာ ထပ်ထည့်သည် — Zin ပေးသော ZAE reference
 #    (`1.mp4`) ရဲ့ စာတန်းကို တိုင်းတော့ **em ၀.၀၄၃** ထွက်သည်。
 "xs": (0.0430, "အသေးဆုံး", "Tiny"),
 "s":  (0.0535, "သေး",      "Small"),
 "m":  (0.0650, "အလတ်",     "Medium"),
 "l":  (0.0800, "ကြီး",     "Large"),
 "xl": (0.0950, "အကြီးဆုံး","Extra large"),
}
MUSIC = [None, "trending", "upbeat", "calm", "folk", "corporate"]
# ⚠️ Latin ဖောင့် — render မှာ **တကယ် ရှိတာပဲ** ဖြစ်ရမည်。 မရှိတာ ပေးလျှင်
#    ffmpeg က တိတ်တဆိတ် အစားထိုးပြီး စာလုံး အရွယ် လွဲသွားသည်。
LATIN = ["Figtree", "Figtree-Bold", "Figtree-Black", "Manrope", "ArchivoBlack",
         "Outfit-Bold", "Outfit-Black"]
CAPSTYLE = ["zae", "big", "plain", "light", "karaoke", "accent"]

# MotionKit ကတ် ၄၇၉ ခုလုံးကို planner ဆီ တိုက်ရိုက်ဖွင့်ပေးလျှင် required props
# မကိုက်ခြင်း၊ မျက်နှာပေါ်ဖုံးခြင်း၊ style မညီခြင်း ဖြစ်နိုင်သည်။ User က မိမိ
# brand အတွက် ရွေးချယ်နိုင်ရမည်၊ renderer ကတော့ စစ်ပြီးသား template family ကိုသာ
# သုံးရမည်။ အောက်က preset တစ်ခုကို Style settings မှာ သိမ်းနိုင်သည်။
MOTIONKIT_PROFILES = {
    "premium": dict(my="Premium balanced", en="Premium balanced",
                    detail_my="hook · callout · data · cinematic motion ကို မျှတစွာ",
                    detail_en="Balanced hook, callout, data and motion"),
    "clean": dict(my="Clean brand", en="Clean brand",
                  detail_my="သန့်ရှင်း၊ brand/business အတွက် motion နည်းနည်း",
                  detail_en="Restrained, brand-safe visual language"),
    "bold": dict(my="Bold creator", en="Bold creator",
                 detail_my="hook၊ number နဲ့ emphasis ကို ပိုပြတ်သားစေ",
                 detail_en="Stronger hooks, numbers and emphasis"),
    "explainer": dict(my="Explainer", en="Explainer",
                      detail_my="steps · checklist · fact ကို ဦးစားပေး",
                      detail_en="Prioritises steps, checklists and facts"),
}

# ⚠️ **`NATURAL` ကို ဒီဖိုင်ထဲမှာပဲ သတ်မှတ်ရမည်**。 `core/grade.py` ထဲ ထားပြီး
#    `get()` က import လုပ်ခဲ့ရာ **server မှာ `/api/styles` တစ်ခုလုံး ပျက်**ခဲ့သည်
#    (၂၀၂၆-၀၉-၂၀)。 Docker image ထဲ `core/` ရဲ့ ၆ ဖိုင်သာ ပါပြီး `grade.py`
#    မပါသဖြင့် flat ရော package ရော import မရ — `except ImportError` ရဲ့
#    ထဲက import ကလည်း ImportError ပြန်ထွက်သွားသည်。 ⇒ ဘောင်တွက် ကိန်းများကို
#    **API ဘက်ရောက်သော ဖိုင်ထဲ**မှာ ထားရမည်、render module ထဲ မထားရ。
NATURAL = dict(
    lv_imin=0.03, lv_imax=0.97, lv_omin=0.02, lv_omax=1.0,
    curve="0/0 0.25/0.245 0.50/0.51 0.75/0.765 1/1",
    cbal=False, sat=1.0, vign=0.0,
)

# field → (အမျိုးအစား, အနိမ့်, အမြင့်)
BOUNDS = dict(
 fps      = ("choice", [24, 30]),
 gfx      = ("int",   0, 30),
 broll    = ("int",   0, 20),
 # ⚠️ ရုပ်ကြမ်း ဘယ်လောက် စားမလဲ — ZAE က ၀.၆၂ (တိုင်းထားသည်)
 broll_pct= ("float", 0.0, 0.85),
 # ⚠️ clip တစ်ခုရဲ့ အများဆုံး အရှည် — ၃.၂s ကန့်သတ်က segment (~၆.၅s)
 #    ထက် တိုသဖြင့် ခွင့်ပြုချက် ကုန်အောင် မသုံးနိုင်ခဲ့。
 broll_max= ("float", 1.0, 8.0),
 cap_pct  = ("float", 0.035, 0.110),   # frame အမြင့်၏ ၃.၅–၁၁%
 cap_base = ("float", 0.550, 0.870),   # ⚠️ ၀.၈၇ ကျော်လျှင် စာတန်း အောက်ထွက်မည်
 stroke_w = ("float", 0.0,   0.30),
 # ⚠️ house band −15.5..−13.5 (target −14.5)。 −17.7 က feed အတွက်
 #    ရွေးစရာ အဖြစ် ကျန်ထားသည် — ဒါပေမယ့် platform က ပြန်တင်မည်။
 lufs     = ("choice", [-13.5, -14.0, -14.5, -16.0, -17.7]),
 music    = ("choice", MUSIC),
 captions = ("choice", CAPSTYLE),
 # ⚠️ ၀ = စာတန်း မပါ · ၁ = အားလုံး。 knowledge က ၀.၁၅ (တိုင်းထားသည်)
 cap_cover= ("float", 0.0, 1.0),
 latin    = ("choice", LATIN),
 scrim    = ("bool",),
 # ⚠️ grade — playbook ရဲ့ ဘောင်အတွင်းသာ
 sat      = ("float", 0.90, 1.30),
 vign     = ("float", 0.0, 0.90),
 cbal     = ("bool",),
 grade    = ("bool",),
 # ⚠️ B-roll နှစ်ခုကြား ပြောသူကို အနည်းဆုံး ဘယ်လောက် ပြရမလဲ
 broll_gap= ("float", 0.4, 8.0),
 broll_tail=("float", 0.0, 15.0),
 # ⚠️ စာတန်း အရောင် — `#RRGGBB` သာ။ ပုံမှန်က theme ရဲ့ WHITE/SUB_STROKE。
 #    အရောင် ပြောင်းလျှင် **ဖတ်ရလွယ်မှု** ကို ကိုယ်တိုင် စစ်ရမည် —
 #    အဖြူနံရံပေါ် အဖြူစာက မမြင်ရ (ZAE မှာ တကယ် ဖြစ်ခဲ့)。
 cap_fill  = ("hex",),
 cap_stroke= ("hex",),
 cap_gap  = ("float", 0.05, 0.80),
 cap_wide = ("float", 0.35, 0.95),
 cap_fade = ("float", 0.0, 0.60),
 # ⚠️ ဘောင် 0.6–1.2/min — REF-A 1.1 · REF-B 0.6 (တိုင်းထားသည်)。
 #    1.5 ကျော်လျှင် skill ရဲ့ P3 က ထုတ်ခွင့် ပိတ်သည်。
 sfx_per_min=("float", 0.0, 1.5),
 # ⚠️ စာတန်းတစ်ကတ် အများဆုံး ဘယ်လောက် ရပ်နိုင်လဲ
 cap_hold = ("float", 1.5, 8.0),
 # ⚠️ ကွက်လပ် ဖြည့်ရန် အနည်းဆုံး လိုအပ်သော ကိုက်ညီမှု အမှတ်
 broll_minscore=("float", 0.0, 12.0),
 # ⚠️ levels — အလင်း များသော footage မှာ imax တင်ရသည်
 lv_imin  = ("float", 0.0, 0.40),
 lv_imax  = ("float", 0.50, 1.0),
 lv_omax  = ("float", 0.80, 1.0),
 lv_omin  = ("float", 0.0, 0.30),
 sfx      = ("bool",),
 cap_typo = ("float", 0.0, 0.6),
 cut      = ("choice", list(CUTS)),
 slide_amt= ("choice", list(SLIDE_AMT)),
 pace     = ("choice", list(PACE)),
 zoom_amt = ("float", 0.0, 0.12),
 energy   = ("choice", ["minimal", "standard", "dynamic"]),
 broll_freq = ("choice", ["low", "normal", "high"]),
 motion   = ("choice", ["low", "normal", "high"]),
 motionkit_profile = ("choice", list(MOTIONKIT_PROFILES)),
 sfx_on   = ("bool",),
 autocut  = ("bool",),
 review   = ("bool",),
 shot_grade = ("bool",),
 silence_ms = ("int", 150, 1200),
)

def cut_name(r):
    """recipe ရဲ့ (keep_pause, min_sil) → ဖြတ်မှု အမည်"""
    kp, ms = r.get("keep_pause"), r.get("min_sil")
    for k, (a, b) in CUTS.items():
        if a == kp and b == ms: return k
    return "custom"

def clean(over):
    """သုံးစွဲသူ ပို့လာသော ပြင်ချက်ကို **စစ်ပြီး** ဘောင်အတွင်း ချသည်。

    မသိသော field · ဘောင်ပြင် တန်ဖိုး → **ဖြုတ်ပစ်သည်** (ကျဘမ်း မလုပ်ဘူး)。
    """
    out = {}
    for k, v in (over or {}).items():
        b = BOUNDS.get(k)
        if not b: continue
        t = b[0]
        try:
            if t == "bool":
                out[k] = bool(v)
            elif t == "int":
                out[k] = max(b[1], min(b[2], int(v)))
            elif t == "float":
                out[k] = max(b[1], min(b[2], float(v)))
            elif t == "hex":
                # ⚠️ အရောင်ကို **ပုံစံ စစ်ရမည်** — မမှန်လျှင် ffmpeg filter
                #    တစ်ခုလုံး ပျက်ပြီး render က ရပ်သွားမည်。
                import re as _re
                v = str(v).strip()
                if not v.startswith("#"): v = "#" + v
                if _re.fullmatch(r"#[0-9A-Fa-f]{6}", v): out[k] = v.upper()
            elif t == "choice":
                opts = b[1]
                if isinstance(v, str) and v.lower() in ("none", "", "null"): v = None
                if v in opts: out[k] = v
                else:
                    # ⚠️ float နှိုင်းတာ တိတိကျကျ မကိုက်နိုင် — အနီးဆုံး ယူသည်
                    nums = [o for o in opts if isinstance(o, (int, float))]
                    if nums and isinstance(v, (int, float)):
                        out[k] = min(nums, key=lambda o: abs(o - v))
        except (TypeError, ValueError):
            continue
    if "stroke" in (over or {}):
        sv = over["stroke"]
        if sv in (None, "", "none"): out["stroke"] = None
        elif isinstance(sv, str) and len(sv) == 7 and sv[0] == "#":
            out["stroke"] = sv
    if "mmf" in (over or {}):
        try:
            import fonts as _FN
            if _FN.ok(str(over["mmf"])): out["mmf"] = str(over["mmf"])
        except Exception:
            pass
    return out

def apply(name, over):
    """recipe + ပြင်ချက် → တကယ် သုံးမည့် ဇယား"""
    r = get(name)
    # ⚠️ **recipe နာမည်ကို ပါသွားစေရမည်** — `label` က ပြရန်သာ ("Headtop")
    #    ဖြစ်ပြီး ပုံစံအလိုက် မူဝါဒ (SFX သိပ်သည်းမှု စသည်) က id နဲ့ ရှာသည်。
    #    မပါလျှင် တိုင်းထားသော profile ကို ဘယ်တော့မှ မတွေ့ပါ。
    r["_id"] = (name or "").strip() or "cinematic-vlog"
    o = clean(over)
    cn = o.pop("cut", None)
    if cn in CUTS:
        r["keep_pause"], r["min_sil"] = CUTS[cn]
    # ⚠️ UI က ms နဲ့ ပို့သည် — engine က စက္ကန့်。 **ဒီမှာ ပြောင်းရမည်**
    #    (`_expand()` က `min_sil` ကနေ တစ်လမ်းသွားသာ တွက်သဖြင့်)。
    _sm = o.pop("silence_ms", None)
    if _sm:
        r["min_sil"] = round(float(_sm) / 1000.0, 3)
    r.update(o)
    _expand(r)                 # ⚠️ ပြင်ချက် ပေါင်းပြီးမှ ပြန်ဖြန့်ရမည်
    return r

def listing():
    """UI အတွက် — ပုံစံတိုင်းရဲ့ တိုင်းထားသော ပုံသေ"""
    out = []
    for k, v in R.items():
        if k in HIDDEN: continue      # ပေါင်းထားပြီး — UI မှာ မပြ
        r = get(k)
        out.append(dict(id=k, label=r["label"], theme=r["theme"], fps=r["fps"],
                        cut=cut_name(r), captions=r["captions"], gfx=r["gfx"],
                        broll=r.get("broll") or 0,
                        broll_pct=r.get("broll_pct"),
                        broll_max=r.get("broll_max"), music=r.get("music"),
                        cap_pct=r.get("cap_pct"), cap_base=r.get("cap_base"),
                        stroke=r.get("stroke"), stroke_w=r.get("stroke_w") or 0.0,
                        lufs=r["lufs"], scrim=bool(r.get("scrim")), mmf=r["mmf"],
                        latin=r.get("latin") or "Figtree-Black",
                        cap_cover=r.get("cap_cover"), cap_typo=r.get("cap_typo"),
                        cap_fill=r.get("cap_fill"), cap_stroke=r.get("cap_stroke"),
                        # ⚠️ ပေါင်းထားသော ပုံစံရဲ့ ပြင်းအား — UI မှာ select ပြရန်
                        slide_amt=r.get("slide_amt"), pace=r.get("pace"),
                        # ⚠️ Headtop ရဲ့ ထိန်းချုပ်ချက်များ — `BOUNDS` မှာ
                        #    စစ်ပြီးသား ဖြစ်ပါလျက် **UI က မမြင်ရ**ခဲ့သဖြင့်
                        #    သုံးစွဲသူ ပြင်လို့ မရခဲ့ပါ (၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့)。
                        #    ⇒ ဒီမှာ မထုတ်ပေးလျှင် `sopen()` က ပြစရာ မရှိပါ。
                        plan=bool(r.get("plan")),
                        energy=r.get("energy"), motion=r.get("motion"),
                        motionkit_profile=r.get("motionkit_profile") or "premium",
                        sfx_on=r.get("sfx_on"), autocut=r.get("autocut"),
                        review=r.get("review"),
                        broll_freq=r.get("broll_freq"),
                        zoom_amt=r.get("zoom_amt"),
                        silence_ms=r.get("silence_ms"),
                        shot_grade=r.get("shot_grade")))
    return out


# ══════════════════════════════════════════════════════════════════════
# Visuals & Motion — အလှအပ **အဆင့်** (၂၀၂၆-၀၉-၂၁ Zin)
# ══════════════════════════════════════════════════════════════════════
# ⚠️ **QC ဂိတ်ကို လုံးဝ မထိရ** (Zin: 「ဂိတ် မလျှော့ရ」)。 ဒါကြောင့်
#    `gfx_share` (coverage ဘောင် — QC က ဒီဘောင်နဲ့ စစ်သည်) ကို **မရွှေ့**ပါ。
#    ရွှေ့တာက **rate** — ဂရပ်ဖစ် အရေအတွက်、B-roll、punch-in、SFX သိပ်သည်းမှု。
# ⚠️ ဒါက တိုင်းချက်အပေါ် အခြေခံသည်: coverage တူတူဆိုပေမယ့် ကတ် ၈ ခုက
#    ၁၆ ခုနဲ့ လုံးဝ မတူ — 「coverage ကို ကြာချိန်နဲ့ ဖြည့်လျှင် slideshow」
#    ဖြစ်ကြောင်း အရင် တိုင်းပြီးသား。 ⇒ rate က တကယ့် လက်ကိုင်。
# ⚠️ SFX သိပ်သည်းမှုကို တင်လျှင် **QC ceiling အထိသာ** — ceiling ကို
#    မတက်စေရ (မတက်ရင် render က QC မအောင်ဘဲ ပိတ်မိမည်)。
LEVELS = ("auto", "minimal", "balanced", "high")
SFX_CEIL = 1.5              # = qc.SFX_MAX_PER_MIN (import ဝိုင်း မဖြစ်စေရန်)
GFX_CEIL = 24               # ကတ် အရေအတွက် — ဒီထက် ပိုလျှင် တစ်ခုချင်း
                            # ကြာချိန် `card_len` ဂိတ် (၁.၀s) အောက် ကျနိုင်
ZOOM_CEIL = 0.12            # punch-in — ဒီထက် ပိုလျှင် မျက်စိ ရှုပ်သည်

# level → (gfx, broll, broll_pct, zoom_amt, insert_per_min, sfx_per_min)
_MUL = {
    "minimal":  (0.50, 0.50, 0.60, 0.00, 0.50, 0.50),
    "balanced": (1.00, 1.00, 1.00, 1.00, 1.00, 1.00),
    "high":     (1.60, 1.30, 1.15, 1.50, 1.50, 1.50),
}


def motion(r, level):
    """`r` ကို အလှအပ အဆင့်အလိုက် ချိန်ညှိသည် — **အသစ် ပြန်ပေးသည်**。

    `auto` · `balanced` · မသိသော level ⇒ recipe ရဲ့ တိုင်းထားသော ပုံသေအတိုင်း。
    ⚠️ `gfx_share` · `cap_*` · `lufs` · grade **မထိပါ** — QC ဂိတ်များ ဖြစ်သည်。
    """
    lv = (level or "auto").strip().lower()
    if lv not in _MUL or lv in ("auto", "balanced"):
        r = dict(r); r["_motion"] = lv if lv in LEVELS else "auto"
        return r
    g, b, bp, z, ins, sx = _MUL[lv]
    r = dict(r)
    if r.get("gfx") is not None:
        r["gfx"] = max(1, min(GFX_CEIL, int(round(float(r["gfx"]) * g))))
    if r.get("broll") is not None:
        r["broll"] = max(0, int(round(float(r["broll"]) * b)))
    if r.get("broll_pct") is not None:
        r["broll_pct"] = round(min(0.60, float(r["broll_pct"]) * bp), 3)
    if r.get("zoom_amt") is not None:
        r["zoom_amt"] = round(min(ZOOM_CEIL, float(r["zoom_amt"]) * z), 4)
    if r.get("insert_per_min") is not None:
        r["insert_per_min"] = round(float(r["insert_per_min"]) * ins, 3)
    if r.get("sfx_per_min") is not None:
        # ⚠️ ceiling အထိသာ — QC `sfx_density` ဂိတ်ကို မဖြတ်စေရ
        r["sfx_per_min"] = round(min(SFX_CEIL, float(r["sfx_per_min"]) * sx), 3)
    r["_motion"] = lv
    return r
