# ZAE Short: Caption ကျော်မှု · true peak · MMS · /Volumes/a (2026-09-27)

ကိန်းပဲ ပါပါတယ်။ ပြင်ချက် မတင်ပြပါ။

## Render အချက်အလက်

- Render: `skip.mp4` (scratchpad) · recipe `short-916` @ `97118f6` (`cap_base` 0.805 · `stroke_w` 0.30)
- seed = job id = `t_s916_pin` · `worker/run.py` = HEAD copy
- Harness က `captions.track` နဲ့ `captions.word_cards` ကို wrap လုပ်ထားပါတယ်။ Pipeline ဆောက်တဲ့ ကတ်အားလုံး (word cards) နဲ့ ffmpeg ကို ပို့တဲ့ concat list ကို ဖိုင်ထဲ ချထားပါတယ်။ IKKI ကုဒ်ကို မပြင်ပါ။
- Concat → burn-in ကွာခြားမှုကို ယခင်က ±1 frame (n = 72) လို့ တိုင်းထားပါတယ်။ ⇒ concat ထဲမှာ ပါ/မပါ = screen ပေါ်မှာ ပေါ်/မပေါ် ဖြစ်ပါတယ်။ ပျောက်တဲ့ ၃ ခုကို frame နဲ့လည်း အတည်ပြုထားပါတယ်။

## ① Caption ကျော်မှု (ကတ် 91 ခု · ASR segment 20 ခု)

| အမျိုးအစား | n | မှတ်ချက် |
|---|---|---|
| အချိန်မှန် ပေါ် (on ±0.06s) | 68 | |
| နောက်ကျ ပေါ် | 4 | 3 ခုက graphic ပြီးမှ ပေါ် (34.03 · 50.79 · 73.79) · 1 ခုက 2.47 → 2.55 (+0.08 · ယခင်ကတ် ထပ်လို့) |
| graphic ပေါ်ချိန် လုံးဝ ဖျောက် (`hide`) | 14 | segment 7 · 11 · 13 · 17 · 19 ရဲ့ ကတ်တွေ (graphic 5 ခုအောက်) |
| graphic နဲ့ တစ်စိတ်တစ်ပိုင်း ထပ်ပြီး မပေါ် | 2 | 42.16–43.16 · 66.96–68.01 |
| **graphic မပါဘဲ ပျောက် (DROPPED)** | **3** | အောက်မှာ ပြထားပါတယ် |

**DROPPED ၃ ခု (frame နဲ့ အတည်ပြုပြီး):**

| ကတ် | ကြာချိန် | segment | ယခင်ကတ် off − ဒီကတ် on | screen ပေါ်မှာ မြင်ရတာ |
|---|---|---|---|---|
| 2.20–2.47 "Language school" | 0.27s | seg 1 **ပထမကတ်** | **+0.35s** (ယခင် segment ရဲ့ နောက်ဆုံးကတ် 1.80–2.55) | ယခင်စကားလုံး **"တယ်" ကျန်နေ** (2.10–2.44) |
| 22.83–23.00 "ကျောင်းနံနက်တက်ရတဲ့" | 0.17s | seg 6 **ပထမကတ်** | **+0.02s** | 22.86–22.91 **ဗလာ** → 22.97 မှ နောက်ကတ် |
| 67.99–68.16 "အချက်အချာကျပြီး" | 0.17s | seg 18 **ပထမကတ်** | **+0.02s** | 68.02–68.07 **ဗလာ** → 68.13 မှ နောက်ကတ် |

**တူညီချက်:**
- ၃ ခုလုံး (3/3) ASR segment ရဲ့ **ပထမကတ်** ဖြစ်ပါတယ်။
- ကြာချိန် **≤ 0.27s** ပါ။
- **ယခင် segment ရဲ့ နောက်ဆုံးကတ်ရဲ့ off-time က ဒီကတ်ရဲ့ on-time ထက် နောက်ကျပါတယ်** (+0.02 ~ +0.35s)။
- ကတ်ချင်း ထပ်တဲ့ pair **14 ခုလုံး (14/14) segment နယ်နိမိတ်မှာ** ဖြစ်ပါတယ်။ Segment အတွင်းမှာ ထပ်တာ **0 ခု** ပါ။ အများဆုံး ထပ်မှုက 0.35s ပါ။
- စာသား ရှည်မှုနဲ့ မဆိုင်ပါ ("Language school" 15 လုံး · ကျန် ၂ ခုက မြန်မာ စကားလုံး ၁ လုံးစီ)။

**c0003 (Language school) က pipeline caption စာရင်းထဲမှာ ရှိလား:**
- **ရှိပါတယ်**: `word_cards()` က seg 1 ရဲ့ ပထမကတ်အဖြစ် ဆောက်ထားပါတယ် (2.20–2.47)。
- **concat ထဲမှာ မရှိပါ** ⇒ caption ဆောက်တဲ့ အဆင့် မဟုတ်ပါ။ **burn-in list ဆောက်တဲ့ အဆင့် (`captions.track` ရဲ့ timed → concat)** မှာ ပျောက်တာပါ။

**တခြား ကိန်း:**
- Graphic `hide` ကြောင့် caption မပြတဲ့ ကတ် 14 + 2 ခု = စကား **~15.4s** (runtime 77.6s ရဲ့ ~20%) ပါ။ ဒါက နောက်တစ်ဆင့် "caption ဖျောက်တာ" အတွက် ကိန်းပါ။
- Segment ၁ ခု (seg 10 "နံပါတ်နှစ်။" 39.63–39.93) က `word_cards()` = None ⇒ `cards()` fallback ကို သုံးပါတယ်။

## ② True peak −1.8 → −1.1 (Step A vs Step B)

| | Step A | Step B |
|---|---|---|
| ASR (chunk 4 · လုံးရေ) | 2470/3008/2578/1781 | **တူ** |
| graphic ရွေး/တပ် | 8 / 5 (no_room 3 · side_bar 0.4 · chapter 9.8 · stat_title 34.0) | **တူ** |
| `gfx_size_16x9.json` | 616 entry · mtime 2026-09-26 16:04 | **တူ** (run ၂ ခုလုံး 2026-09-27) |
| music track | တူ | တူ |
| **B-roll** | 18.40 · 48.19 · 52.19 · 65.29 … | 48.19 · 52.19 · **58.49 · 67.99** (clip ကွဲ) |
| **SFX cue** | **18** | **16** (role · အချိန် ကွဲ) |
| true peak (4× oversample) | −1.81 @ 9.5–10.0s | **−1.11 @ 9.5–10.0s** |

- Step B peak နေရာ (9.5–10.0s) မှာ SFX: `type_tick` 9.85 · `deep_whoosh` 10.08 (−13 dB) · `latch` 10.30 · `whoosh_in` 10.30 ပါပါတယ်။ Step A ရဲ့ ဒီနေရာမှာ SFX **0**。
- Step B ရဲ့ ဒုတိယ peak −1.55 @ 67.5–68.0s က Step B မှာပဲ ပါတဲ့ B-roll 67.99 ရဲ့ whoosh နေရာပါ။
- ⇒ caption ink နဲ့ မဆိုင်ပါ။ **B-roll (Gemini) ရွေးချယ်မှု ကွဲ → SFX budget ရွေးတဲ့ cue ကွဲ** ပါ။ ဂိတ် ၅ ခုရဲ့ ကိန်း (stroke 0.49→0.87 · edge 2.59→19.46) က ဒီ noise ထက် အများကြီး ကြီးပါတယ်။
- ⚠️ ထပ်တွေ့ချက်: 9.85/10.08/10.30 SFX က **`no_room` နဲ့ ပယ်ခံရတဲ့ `chapter` @9.8 graphic ရဲ့** SFX ဖြစ်ပါတယ် (role deep_whoosh/latch)။ ⇒ screen ပေါ် မပေါ်တဲ့ graphic အတွက် အသံ ထွက်နေပါတယ်။ `dress.py` (shared · TH ပိုင်) ⇒ report ပဲ လုပ်ပါတယ်။

## ③ MMS forced alignment (Burmese) — **စမ်းပြီး မရ**

- Setup: torchaudio 2.11 `MMS_FA` (315M param) + `uroman` romanization · Python 3.14 venv (scratchpad · ပြီးတာနဲ့ ဖျက်ပြီး)
- `ctc-forced-aligner` က py3.9 မှာ မရ (≥3.10 လို) · py3.14 မှာ build မရ
- Clip: output 20–50s (source voice-only · lag +0.1437) · Gemini စကားလုံး 47 ခု → align 46 ခု · score median **0.368** (p10 0.217)
- Ground truth ၃ နေရာ (ရပ်ပြီးမှ စတဲ့ acoustic onset):

| GT | Gemini Δ | MMS Δ |
|---|---|---|
| 28.14 | −0.14 | **+0.53** |
| 39.73 | −0.10 | **−0.70** |
| 43.13 | +0.03 | **+0.81** |

- ⇒ MMS က onset နေရာမှာ **စကားလုံး တစ်လုံး ရွေ့ပြီး** တွဲပါတယ်။ Gemini ထက် မှားပါတယ် (MMS−Gemini: a +0.53 · b −0.0063)。 ⇒ ဒီ source မှာ n = 20/20 ground truth အဖြစ် သုံးလို့ မရပါ။ အချိန် ~10 မိနစ်။

## ④ /Volumes/a

- **ဘယ်သူမှ unmount မလုပ်ပါ။** 2026-09-26 **21:29:20** kernel: `disk4s2: device/channel is not attached · media is not present` ⇒ device ကိုယ်တိုင် ပြုတ်သွားတာပါ (ကြိုး/ပါဝါ/USB)。 21:29:21 diskarbitrationd က removed · 21:29:23 မှ unmounted (cleanup)。
- 15:00–17:40 ကြား unmount/eject/force event **0** ⇒ 21:29 အထိ mount ရှိခဲ့ပါတယ်။
- ယခု: mount မရှိ · `diskutil list external` = disk မရှိ · /Volumes/a သုံးနေတဲ့ process 0 ခု。
- ကျွန်တော့ ယခင် "unmount လုပ်ထား" ဆိုတဲ့ စကားက **မှားပါတယ်** (ပျောက်နေတာကို ခန့်မှန်းခဲ့တာ)။ Mount/unmount ကို ကျွန်တော် မလုပ်ခဲ့ပါ။
