# Reference r3 (Recent Visual Editing Trends) vs IKKI Short render ③ — layer ၅ ခု တိုင်းတာ (2026-09-27)

ကုဒ် မပြင်ပါ။ တိုင်းတာပဲ လုပ်ပါတယ်။ ဗီဒီယို: `~/Downloads/IKKI_vs_reference_r3_compare.mp4` (84 s · ဘေးချင်းယှဉ် · event label တွေ တိုင်းထားတဲ့ အချိန်မှာ ပေါ် · ပထမ 42 s = reference အသံ · ဒုတိယ 42 s = IKKI အသံ)

## Detector တွေကို အရင် စစ်ခဲ့ပုံ (အဖြေသိပြီးသား ဖိုင်နဲ့)

| detector | စစ်ပုံ | ရလဒ် |
|---|---|---|
| cut | render ③ B-roll အစ/အဆုံး 18 ခု (log) | 18/18 (±0.1 s) · အပို 15 ခုက frame နဲ့ ကြည့်တော့ jump cut / whip / graphic ဝင်ချိန် (အစစ်) |
| camera motion (global Gauss-Newton) | PIL နဲ့ ဆောက်ထားတဲ့ subpixel အတိအကျ move 5 ခု | 4/5 က 1% အတွင်း (pan 90.1/90 px · zoom +14.9/15% · +8.1/8% · −10.0/−10%) · 5 ခုမြောက်က synthetic ကိုယ်တိုင် ပုံအစွန်း ကျော် · ⚠️ အလွန်နှေးတဲ့ zoom (~0.15 px/frame) ကို ~½ လျော့တိုင်း ⇒ IKKI zoom ကို code ကနေ ယူ |
| caption ပြောင်းချိန် | render ③ concat list (107 ပြောင်းချိန်) | 106/107 · ±1 frame · အပို 11 (precision ~90%) |
| SFX (whoosh အမျိုး ≥0.15 s) | demucs နဲ့ အသံခွဲ → 1.5–16 kHz · render ③ whoosh 6 ခု + **holdout** (r3 အသံထဲ SFX 12 ခု ထည့်) | ③ 6/6 · holdout whoosh 7/8 · pop 3/4 · **false 0** |
| SFX တိုတို (tick/click) | render ③ tick 3 · click 3 | **0/3 — တိုင်းလို့ မရ** (ဗျည်းသံ ယိုစိမ့်) ⇒ spectrogram မျက်စိနဲ့ပဲ |
| title | mask detector က grey-gradient စာကို မမိ ⇒ | frame (15 fps) မျက်စိနဲ့ ရေတွက် |

⚠️ Mixed audio ပေါ်မှာ တိုက်ရိုက် SFX ရှာတာ **precision 3–5%** ဖြစ်လို့ မသုံးပါ (ယခင် memory နဲ့ တူ)။

## Layer ၅ ခု

### ① Edit (ဖွဲ့စည်းပုံ · cut)

| | r3 (42.2 s) | IKKI ③ (77.6 s) |
|---|---|---|
| အကြောင်းအရာ | ပြောသူ 0–2.7 s + 39.2–42.2 s ပဲ · **~85% = ဖုန်း UI screen** (သူများ post · gallery · chat bubble) | ပြောသူ + B-roll 9 ခု (22.5 s · 29%) + graphic ကတ် 5 |
| hard cut | 13 (18.5/min): ပြောသူ↔screen 2 · screen လဲ ~5 · post ထဲက clip ကိုယ်တိုင် ~6 | 34 (26/min): B-roll edge 18 + jump cut + whip |
| ⇒ | "edit" အများစုက cut မဟုတ်ဘဲ **UI motion** | cut ပိုများ (နည်းတာ မဟုတ်) |

### ② Motion (camera)

| | r3 | IKKI ③ |
|---|---|---|
| ဒီဇိုင်းထားတဲ့ move | **7 ခု**: push-in **+53% / 0.9 s** (intro) · zoom-in **+18% / 1.0 s** · pull-out **−26% / 1.4 s** (outro) · zoom-out −11% / 0.5 s · −8% / 1.4 s · slide-out 18%W / 1.0 s · slide-in 15%W / 0.8 s | **0** · slow breathing zoom 1.00→1.08× (40 s cycle · 16% of time · code) |
| easing | **ease-out အဓိက** (first-half share 0.80–0.97: 4/7) · slide-out က ease-in (0.21) | cosine (ease-in-out) |
| ကြာချိန် | 0.5–1.4 s | ~3.2 s push + 3.2 s pull |

### ③ Animation (စာ)

| | r3 | IKKI ③ |
|---|---|---|
| section title | 4 group + intro + outro · **ပြောတဲ့ စကားလုံးနဲ့ lock** (FREEZE 3.97 vs 3.99 · FRAME 4.37 vs 4.35) · blur+fade in **0.27 s** · နောက်စကားလုံး **+0.4 s** stack · hold 1.0–1.2 s · fade out 0.3 s · အဖြူ + dark soft shadow · ထိပ် | **မရှိ** |
| graphic ကတ် | 3D icon pop (intro) · post card 3D tilt ဝင် · comment pill (outro) | side_bar/chapter/step_flow/stat_title 5 ခု · ဝင် 0.45 s · 3 ခု no_room နဲ့ ပယ် |

### ④ Timing (caption)

| | r3 | IKKI ③ |
|---|---|---|
| စကားလုံး / ကတ် | **1.6** (1–3: "take a" · "from a video" · "it on") | 1.24 (Burmese ASR word) |
| ကတ် / s | **2.3** (interval p50 0.30 s) | 1.07 (interval p50 0.69 s · ကတ် p50 0.66 s) |
| ပေါ်ချိန် vs စကား | median −17 ms (p10/p90 ±90 ms · whisper word timing ကိုယ်တိုင် ±) | speech onset = 0 ms (G1) |
| screen ပေါ် % (body) | 77% | 78% |
| y · style | 0.784 · white bold + black soft shadow | 0.805 · white + stroke |
| စကား ပြော 속도 | 3.8 words/s (English) | — |

### ⑤ Sound

| | r3 | IKKI ③ |
|---|---|---|
| whoosh အမျိုး SFX | 5 ခု · 7.1/min (intro→screen riser 0.8 s · 15.1 · 34.8 · outro ×2) | 11 ခု · 8.5/min |
| tick/sparkle | title build တွေမှာ ~11 kHz tick train (0.3–1.3 s · ~12 s) — spectrogram မျက်စိ · **အရေအတွက် မတိုင်နိုင်** | type_tick (log) |
| **music** | lo-fi beat တစ်လျှောက် · music **−24.8** vs voice −16.6 LUFS = **~8 dB အောက်** | music **−31.1** vs voice −14.4 = **~17 dB အောက်** |
| loudness | −14.9 LUFS | −14.2 LUFS |

## ကွာဟချက် — အကြီးဆုံးကနေ

1. **အကြောင်းအရာ (85% UI screen)** — customer footage ကနေ ပြန်ထုတ်လို့ **မရ** (content ပါ · edit effect မဟုတ်)။
2. **ဒီဇိုင်းထားတဲ့ camera move** — r3 7 ခု (0.5–1.4 s · ease-out) vs IKKI 0။ ဆောက်လို့ရ (key moment မှာ push-in/pull-out/slide)။
3. **စကားလုံး lock title** — r3 မှာ section တိုင်း · IKKI မရှိ။ word timing ရှိပြီးသားမို့ ဆောက်လို့ရ (Burmese title font အတည်ပြုရ)။
4. **Music level** — 8 dB vs 17 dB အောက်။ preset ကိန်း ၁ ခု (`music_lufs` −30)။ ⚠️ Zin ရဲ့ taste (ZJL reference မှာ music မရှိ) နဲ့ ဆိုင်လို့ ဆုံးဖြတ်ချက်လို။
5. **Caption သိပ်သည်းမှု** — 2.3 vs 1.1 cards/s။ ဘာသာစကား (English 3.8 words/s · ကတ် 1–3 လုံး) နဲ့ N=778 px ကြောင့် အများစု · တိုက်ရိုက် မကူးသင့်။
6. **Phone post card frame** — B-roll ကို (brand မပါ) post ကတ်ပုံထဲ ထည့်ပြ — ဆောက်လို့ရ။

**ကွာဟချက် မဟုတ်တာ:** cut အရေအတွက် (IKKI ပိုများ) · caption screen ပေါ် % (77 vs 78) · loudness · whoosh အရေအတွက်။

## ဆုံးဖြတ်ရန်

အထက်က 2–6 ထဲက ဘယ်ဟာ အရင်ဆောက်မလဲ။ တစ်ခုချင်း · ကိန်း before/after နဲ့ · ခွင့်ပြုချက် ရမှ။

## ဖိုင်

- harness: `scratchpad/r3/` (`gmot.py` motion · `capdet.py`+`capev.py` caption · `sfx2.py` + `sep.py` SFX · `compare.py` ဗီဒီယို)
- demucs venv `scratchpad/sepvenv` (795 MB · ကျွန်တော့ scratch · ဖျက်ဖို့ အဆင်သင့်)
