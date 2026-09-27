# Short-form reference ၄ ပုဒ်: graphics တိုင်းတာမှု (2026-09-26)

**နည်းလမ်း:**
- Reference တစ်ပုဒ်ချင်းကို **သီးသန့်** တိုင်းထားပါတယ်။ ပျမ်းမျှ မတွက်ပါ။
- 2 fps frame တိုင်းကို timestamp တပ်ပြီး မျက်စိနဲ့ မှတ်ထားပါတယ်။ ဒါကြောင့် ကြာချိန် resolution က ±0.5s ပါ။
- ပြောနေတဲ့ စကားလုံးကို whisper.cpp (large-v3-turbo) နဲ့ စကားလုံး timing ယူထားပါတယ်။
- Sheet: `/Volumes/a/ikki_test916/ref/ann_r*.png`

r1 = TRENDING Motion Graphic (15.4s) · r2 = $40 vs $200 editor (62.3s) · r3 = Recent Visual Editing Trends (42.2s) · r4 = Podcast Into Reels (16.6s)

## အဓိပ္ပာယ် (ကိန်းတွေ ကွာနိုင်လို့ ၂ မျိုး ခွဲထားပါတယ်)

- **Overlay ကတ်** = ပြောသူ မြင်နေရချိန်မှာ ထပ်တင်တဲ့ graphic။ Brief ရဲ့ r3 "4.3/min" က ဒီအဓိပ္ပာယ်ပါ။ ကတ် 3 ÷ 42.2s = **4.3** တိတိ ကိုက်ပါတယ်။
- **Graphic အားလုံး** = overlay + frame အပြည့် graphic (motion card · kinetic-type slide · UI mockup)။ Footage B-roll နဲ့ glitch/flash transition ကို **မပါပါ**။
- **ကတ်အသစ်** = graphic အသစ် ဝင်လာတာ။ **ယူနစ် တည်ဆောက်** = ရှိပြီးသား ကတ်ပေါ်မှာ element ထပ်တိုးတာ (icon တစ်ခု · စာကြောင်း တစ်ကြောင်း · glow)။

## ပုဒ်တစ်ခုချင်း

| | r1 | r2 | r3 ⚠️ | r4 | **IKKI v4** |
|---|---|---|---|---|---|
| ပြောသူ မြင်ရချိန် | ~6% (4.5–5.4s) | ~70% | ~12% (အစ/အဆုံး) | ~35% | ~75% |
| **overlay ကတ် /min** | 0 | **8.7** (9) | **4.3** (3) | 0 | **6.2** (8) |
| ကတ်အသစ် (အားလုံး) /min | 27.3 (7) | 14.4 (15) | 19.9 (14) | 25.3 (7) | 6.2 (8) |
| ဝင်ချိန် အားလုံး (ကတ်+ယူနစ်) /min | 54.5 (14) | 26.0 (27) | ~41 (29) | 72.3 (20) | 6.2 (8) |
| စခရင်ပေါ် ရှိချိန် (runtime %) | 84% | 44% | 97%* | 61% | ~27% |
| ကတ် median ကြာချိန် | 1.5s | 1.5s | ~2–3s | 1.5s | ~3s |
| **ယူနစ်လိုက် တည်ဆောက်** % | 50% | 44% | ~52% | 65% | **0%** |
| graphic y (overlay) | frame အပြည့် · အလယ် | 0.47–0.67 (median 0.52) | 0.2–0.8 | frame အပြည့် | 0.55–0.80 |
| မျက်နှာ ထပ်မှု (graphic) | 0% | 0% (ကတ်တွေ မေးအောက် ရင်ဘတ်ပေါ်) | 0% | cutout ကိုယ်တိုင်က graphic | ~0% |
| caption + graphic တစ်ပြိုင်နက် (graphic ချိန်၏) | 69% | ~47% | UI ပေါ် ~90% | **0%** (graphic ကိုယ်တိုင်က စာ) | ~0% (caption 41 ကတ် ဖျောက်) |
| caption y (median · detector) | 0.67 | **0.50** | 0.63† | 0.55 | 0.60 → ယခု 0.78 base |
| caption stroke | အနက် ပါးပါး | **မရှိ** (shadow) | မရှိ (shadow) | မရှိ | အနက် ပါး (0.10) |
| graphic စာသား = ပြောတဲ့ စကားလုံး | 4/6 (67%) | 3/11 (27%) | ခေါင်းစဉ်တွေက စကားလုံး · UI စာက မဟုတ် | **100%** (kinetic transcript) | Gemini ကောက်နုတ်ချက် |

\* r3 မှာ UI screen-recording ကိုပါ graphic အဖြစ် ရေတွက်ထားပါတယ်။ Overlay ကိုပဲ ရေတွက်ရင် ~11% ပါ။

† r3 ရဲ့ caption detector က UI ပေါ်က စာကိုပါ ယူမိနိုင်လို့ ကိန်းက ညစ်ညမ်းနိုင်ပါတယ်။

Caption stroke: r2/r3/r4 က stroke မသုံးပါ။ ဒါကြောင့် detector ရဲ့ "dark rim" ကိန်း (0.61–1.49) က **stroke မဟုတ်ဘဲ အမှောင် နောက်ခံ** ကို တိုင်းမိတာပါ။ v4–v8 ရဲ့ stroke ratio နဲ့ **တိုက်လို့ မရပါ**။ Stroke ပစ်မှတ်ကို Zin ရဲ့ ZAE ဗီဒီယိုကနေပဲ ယူရပါမယ် (0.90)။

## Trigger: ဘယ်စကားမှာ ချလဲ · ဘယ်နေရာမှာ မချလဲ

**r1:** စကားလုံး အဓိကတိုင်းမှာ ချပါတယ်။ Trigger ဖြစ်တဲ့ စကားလုံးတွေက: trending · graphs · important · expensive software · After Effects · Premiere · CapCut · free · last video။ Graphic မချတာ **၁ ခု** ပဲ ရှိပါတယ်: "complicated" (4.8s · ပြောသူ + caption ပဲ)။

**r2:** Claim တစ်ခုကို ပုံဖော်တဲ့ နေရာမှာ ချပါတယ်။
- ချတဲ့နေရာ: ဈေးနှုန်း နှိုင်းယှဉ် · နာမည်မိတ်ဆက် · "secrets" · "flashy edits" · "sloppy/get clients" · "keep them" · "custom visuals" · "watch longer" · "more money" · "gets results" · "follow me"
- **မချတဲ့ အပိုင်း ၈ ခု:**
  - 8.0–10.4 "the answer goes deeper"
  - 12–16 (ကိုယ်ပိုင် footage)
  - 19.0–23.4 "difference is clear… $40 editor uses cheap assets"
  - 29.0–30.4
  - 32.0–35.4 "other side of the coin"
  - 38.5–42.4 "viral psychology"
  - 44.0–47.9 "learn from it… conversion"
  - 52.5–59.9 "nobody's talking about this… high-performing"
- ⇒ Claim ရှိပေမယ့် မချတဲ့ keyword: "cheap assets" · "viral psychology" · "conversion" · "nobody's talking about"။ ဒီနေရာတွေမှာ caption ရဲ့ **အရောင်ခွဲ keyword** ($40 အနီ · $200 အစိမ်း) ကိုပဲ သုံးပါတယ်။

**r3:** Section တိုင်းရဲ့ အစမှာ ခေါင်းစဉ် ချပါတယ် (FREEZE FRAME · Grow Effect · Match Cut)။ Overlay ကိုတော့ intro + CTA မှာပဲ ချပါတယ်။

**r4:** ဝါကျတိုင်းကို kinetic slide လုပ်ပါတယ်။ **မချတဲ့ အပိုင်း ၂ ခု** ရှိပါတယ်: 7.0–8.4 "change all the things about themselves" နဲ့ 11.5–14.9 "psychological blocks that keep us sounding the same"။ ဒီနေရာတွေမှာ caption keyword "us" ကို အနီကြီးနဲ့ပဲ ပြပါတယ်။

## ⚠️ r3 က outlier လား

**Style မတူပါ။** r3 က "screen-share explainer" ပါ။
- Runtime ရဲ့ 88% က ဖုန်း UI screen-recording (တခြား creator ရဲ့ post တွေ) ဖြစ်ပါတယ်။
- ပြောသူက အစ 2.4s နဲ့ အဆုံး 2.9s မှာပဲ ပေါ်ပါတယ်။
- 4.3/min နိမ့်တာက ပြောသူ မြင်ရချိန် နည်းလို့ပါ။ Graphic နည်းလို့ မဟုတ်ပါ (ကတ်အသစ် 19.9/min)။
- IKKI ရဲ့ talking-head ပုံစံနဲ့ နှိုင်းဖို့ **r2 က အနီးစပ်ဆုံး** ပါ (ပြောသူ 70% · overlay 8.7/min)။
- r1 နဲ့ r4 က motion graphic / kinetic-type ပုံစံ ဖြစ်ပြီး ပြောသူ နည်းပါတယ်။

## IKKI v4 နဲ့ နှိုင်းယှဉ်ချက် (ကိန်း)

| | r2 (အနီးဆုံး) | IKKI v4 | ကွာ |
|---|---|---|---|
| overlay ကတ် /min | 8.7 | 6.2 | ×0.71 |
| ဝင်ချိန် အားလုံး /min | 26.0 | 6.2 | ×0.24 |
| ယူနစ် တည်ဆောက် % | 44% | 0% | IKKI ကတ်တွေ build မလုပ် |
| ကတ် median ကြာချိန် | 1.5s | ~3s | ×2 |
| စခရင်ပေါ် ရှိချိန် | 44% | ~27% | ×0.6 |
| caption + graphic တစ်ပြိုင်နက် | ~47% | ~0% (41 ကတ် ဖျောက်) | IKKI က graphic ပေါ်ရင် caption ဖျောက် |
| graphic y | 0.47–0.67 | 0.55–0.80 | IKKI က caption ဇုန်နဲ့ ထပ် |
| မချတဲ့ ကွက်လပ် အရှည်ဆုံး | 7.5s (52.5–59.9) | ~13s (51–64) | |

**ကိန်းကနေ ဖတ်လို့ရတာ** (အကြံ မဟုတ်၊ ကိန်းသာ):
- **ကတ်အရေအတွက်** (overlay ×0.71) ထက် **ဝင်ချိန် ပမာဏ** (×0.24) က ပိုကွာပါတယ်။ ကွာခြားမှုရဲ့ ~ထက်ဝက်က **ယူနစ်လိုက် တည်ဆောက်တာ** (ကတ်တစ်ခုပေါ်မှာ ၂–၄ ကြိမ် ထပ်တိုး) ကနေ လာပါတယ်။
- r2 မှာ caption နဲ့ graphic က ~47% တစ်ပြိုင်နက် ပေါ်ပါတယ်။ Graphic ကို caption **အောက်** (y 0.50–0.55) မှာ ထားလို့ပါ။ IKKI ကတော့ ဖျောက်ပါတယ်။
- ⛔ ဒီကိန်းတွေကို ကြည့်ပြီး ဘာမှ မပြောင်းရသေးပါ (template ရွေးချယ်မှု · build · hide က shared layer / TH session ပိုင်ပါ)။

## ✅ လုပ်ပြီးတာ: caption ပြင်ချက် (Z2 · Z3)

`short-916` `cap_base` **0.64 → 0.78** (commit `8a88360`)

| | before | after (တွက်ချက်) |
|---|---|---|
| caption band အောက်ခြေ | 1228px (0.64) | **1497px** (0.78) |
| caption band ထိပ် | 876px | 1145px |
| ink အလယ် | 0.60 (တိုင်း v4–v8) | **~0.74** (base − 0.04 · v4–v8 မှာ တိုင်းထားတဲ့ offset) |
| TikTok UI (1600px) · cap_max (1599px) | အတွင်း | အတွင်း |

- ⚠️ Zin ရဲ့ caption **အလယ်** က 0.78 ဖြစ်ပါတယ်။ `cap_base` က band ရဲ့ **အောက်ခြေ** ဖြစ်လို့ ink အလယ်က ~0.74 ပဲ ရောက်ပါမယ်။ 0.78 အတိအကျ လိုရင် `cap_base` ≈ 0.82 ထားရပါမယ် (cap_max 0.833 အတွင်း)။ Zin ဆုံးဖြတ်ရန်ပါ။
- After ကိန်းကို render အသစ်နဲ့ **မတိုင်းရသေးပါ**။ Brief အရ variable မထိန်းဘဲ render မထုတ်ပါ။ Render လုပ်ဖို့ ခွင့်ပြုရင် `IKKI_SEED` pin + ဒီကိန်း တစ်ခုတည်း ပြောင်းပြီး တိုင်းပါမယ်။

## TH session ဆီ

- `tests/test_gfxfit.py` က **ကျနေပါတယ်**: "ပြောသူပေါ် တင်နိုင်သော အစားထိုး သုံးသည်"။
- ကျွန်တော့ `cap_base` ပြင်ဆင်ချက်ကို stash လုပ်ပြီး စမ်းတော့လည်း ကျပါတယ်။ ဒါကြောင့် commit မလုပ်ရသေးတဲ့ shared ဖိုင်တွေ (`assets/gfx_ok.txt` · `core/gfxcat.py` …) ကြောင့် ဖြစ်နိုင်ပါတယ်။
- Z1 အရ မထိထားပါ။
