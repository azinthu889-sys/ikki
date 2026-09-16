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
    sat=1.02, vign=0.65, sfx_per_min=1.0),
 "vlog": dict(label="Vlog", theme="zjl", fps=30,
    keep_pause=0.40, min_sil=0.75, captions="karaoke", gfx=6, music="upbeat",
    mmf="MasterpieceUniRound", latin="Figtree-Black",
    cap_pct=0.0481, cap_base=0.680, lufs=-14.5, cap_max=0.833, scrim=False,
    broll=5, broll_pct=0.30, cap_cover=0.85,
    sat=1.05, vign=0.55, sfx_per_min=1.0),
 "podcast": dict(label="Podcast", theme="zjl", fps=30,
    keep_pause=0.26, min_sil=0.45, captions="karaoke", gfx=2, music=None,
    mmf="MasterpieceUniRound", latin="Figtree",
    cap_pct=0.0444, cap_base=0.680, lufs=-14.0, cap_max=0.833, scrim=False,
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
 "knowledge": dict(
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
    keep_pause=0.18, min_sil=0.34, captions="zae", gfx=5, music="zae",
    mmf="MyanmarHeadOne", latin="Figtree-Black",
    # ⚠️ Zin ရွေးချယ်ချက် (၂၀၂၆-၀၉-၁၃) — နမူနာ ၄ မျိုး (77/93/115/136px)
    #    ကို မြင်ပြီး **136px = 0.095** ကို ရွေးသည်。 N5 project ရဲ့ 0.0535
    #    က ကိန်းအရ ကိုက်ပေမယ့် သူ မြင်ရတာ သေးလွန်းသည် — အမြင်က ကိန်းထက်
    #    အထက်တန်း。
    # ⚠️ စာတန်း ၃၀% ကို typography template နဲ့ ထုတ်သည် — ကျန်တာ
    #    ပုံမှန်。 အားလုံး typography လုပ်လျှင် ဖတ်ရ ပင်ပန်းပြီး
    #    အလေးထားချက် ပျောက်သည်。
    cap_typo=0.30,
    cap_pct=0.100, cap_base=0.865, stroke="#1E3B5A", stroke_w=0.16,
    # ⚠️ −18.8 က N5 reference ကနေ တိုင်းယူထားတာ — ဒါပေမယ့် **reference
    #    ကိုယ်တိုင်က တိုးလွန်း**သည် (skill `ikki-presentation` §8: REF-B
    #    −22.58 ကို "၈ dB အောက်" ဟု ဆိုထားသည်)。 platform တွေက ~−14 ကို
    #    normalise လုပ်သဖြင့် feed ထဲမှာ တခြားဟာတွေထက် တိုးနေမည်。
    #    ⇒ **ဖွဲ့စည်းပုံကို လိုက် · mastering ကို ပြင်**。 လိုလျှင် style editor
    #      ကနေ −17.7 ပြန်ရွေးလို့ ရသည်。
    lufs=-14.5, cap_max=0.870, cap_wide=0.63, sfx=False, scrim=True, broll=10, broll_pct=0.51, broll_max=4.5,
    sat=1.00, vign=0.0, cbal=False, sfx_per_min=0.9,
    lv_imin=0.10, lv_imax=1.0, lv_omin=0.0, curve="none"),
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
    lv_imin=0.10, lv_imax=1.0, lv_omin=0.0, curve="none"),
 "brand-review": dict(label="Brand Review", theme="zjl", fps=30,
    keep_pause=0.40, min_sil=0.75, captions="plain", gfx=9, music="calm",
    mmf="Padauk", latin="Manrope",
    cap_pct=0.0481, cap_base=0.680, cap_cover=0.80, lufs=-14.5, broll=0,
    sat=1.00, vign=0.50, cbal=False, sfx_per_min=0.8),
 "short-biz": dict(label="Short Video", theme="zae", fps=30,
    keep_pause=0.20, min_sil=0.38, captions="big", gfx=6, music="corporate",
    mmf="NotoSansMyanmar-Bold", latin="ArchivoBlack",
    cap_pct=0.0333, cap_base=0.620, lufs=-13.5, broll=0,
    sat=1.00, vign=0.0, cbal=False, sfx_per_min=1.1,
    lv_imin=0.10, lv_imax=1.0, lv_omin=0.0, curve="none"),
 # ⚠️ Course — ဖြတ်တောက် **လုံးဝ မလုပ်ရ**
 "course": dict(label="Course", theme="zjl", fps=30,
    keep_pause=None, min_sil=None, captions="plain", gfx=10, music=None,
    mmf="PadaukBook-Bold", latin="Figtree",
    cap_pct=0.0426, cap_base=0.880, lufs=-14.5, broll=0,
    sat=1.02, vign=0.25, sfx_per_min=0.5),
}
DEF = dict(cap_pct=None, cap_base=None, stroke=None, stroke_w=0.0,
           cap_cover=None, cap_accent=None, broll_pct=0.30, broll_max=3.2,
           sfx=True, cap_typo=0.0, sat=None, vign=None, cbal=True, grade=True,
           broll_gap=3.0, sfx_per_min=None, cap_hold=4.0, broll_minscore=2.0,
           broll_tail=5.0, cap_gap=0.18, cap_fade=0.14, cap_wide=0.86,
           gfx_share=None,
           lv_imin=None, lv_imax=None, lv_omin=None, lv_omax=None, curve=None,
           cap_fill=None, cap_stroke=None,
           lufs=-14.0, cap_max=None, scrim=False, broll=0)

def get(name):
    r = dict(DEF); r.update(R.get(name, R["cinematic-vlog"])); return r


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

# field → (အမျိုးအစား, အနိမ့်, အမြင့်)
BOUNDS = dict(
 fps      = ("choice", [24, 30]),
 gfx      = ("int",   0, 14),
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
    o = clean(over)
    cn = o.pop("cut", None)
    if cn in CUTS:
        r["keep_pause"], r["min_sil"] = CUTS[cn]
    r.update(o)
    return r

def listing():
    """UI အတွက် — ပုံစံတိုင်းရဲ့ တိုင်းထားသော ပုံသေ"""
    out = []
    for k, v in R.items():
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
                        cap_fill=r.get("cap_fill"), cap_stroke=r.get("cap_stroke")))
    return out
