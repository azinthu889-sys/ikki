# ZAE Short: Subtitle Timing တိုင်းတာမှု (အလုပ် ၁) · 2026-09-26

ကုဒ် တစ်လုံးမှ မပြင်ထားပါ။ တိုင်းရုံပဲ လုပ်ထားပါတယ်။ Brief အတိုင်း **ကောက်ချက် မချပါ**။

## Render အချက်အလက်

- `tm.mp4` · recipe `short-916` · source `tokutei.mp4` · **seed = job id = `t_s916_pin`** (cb080/sw030 နဲ့ တူ)
- Code က HEAD `5a047d8` ပါ:
  - `worker/run.py` ကို HEAD ကနေ `/Volumes/a/ikki_test916/code_head/` ကို ကူးပြီး သုံးထားပါတယ်။ ဘာကြောင့်လဲ ဆိုတော့ working tree ထဲက uncommitted font guard (Cinematic session) က render ကို ငြင်းခဲ့လို့ပါ။ အဲဒါကို နောက်ပိုင်း `3267261` မှာ ပြင်ပြီးပါပြီ။
  - `core/` က repo ထဲကအတိုင်း သုံးထားပါတယ်။ `core/gfxcat.py` နဲ့ `core/fonts.py` မှာ uncommitted ပြောင်းလဲမှု ရှိပါတယ်။
- Recipe (committed): `cap_base` 0.80 · `stroke_w` 0.10 · `cap_by_word` · `cap_lines` 1 · `cap_fade` 0
- Harness `h_timing.py` က `captions.track` ကို wrap လုပ်ပါတယ်။ Pipeline က ffmpeg ကို ပေးတဲ့ concat list (`caps.txt`)၊ caption ဆီ ဝင်တဲ့ `caps` + word timing၊ `vplan` ကို ဖိုင်ထဲ ချထားပါတယ်။
- Data ဖိုင်: `/Volumes/a/ikki_test916/tm.mp4.timing.json` · `.timing_result.json` · `.overlay_result.json` · `.gt.json`

## တိုင်းထားတဲ့ အချိန် ၄ မျိုး

| အမည် | ရင်းမြစ် | ground truth လား |
|---|---|---|
| `pipe_on/off` | concat list ရဲ့ duration ပေါင်းစု (ffmpeg ဆီ တကယ် ပေးတဲ့ တန်ဖိုး) | — |
| `gemini_word` | Gemini ASR `words` (cut timeline) — pipeline ကိုယ်တိုင် caption ဆောက်ရာမှာ သုံးတဲ့ ရင်းမြစ် | **မဟုတ်** |
| `burn_on` | output video ကို 30fps frame တိုင်း · caption band (0.68–0.82·H) ထဲက dark-rim အဖြူ pixel ပြောင်းလဲမှု | — |
| `acoustic` | **source audio (voice only)** · ≥120ms တိတ်ပြီးနောက် ≥10dB တက်သံ → output timeline ပေါ် envelope cross-correlation နဲ့ map | **ဟုတ်** (လွတ်လပ်) |

⚠️ **Ground truth ကန့်သတ်ချက်:**
- Myanmar ဘာသာအတွက် forced alignment ကိရိယာ မရှိပါ (whisper က Myanmar ကို မရ)။
- ဒါကြောင့် စကားသံ စတဲ့ နေရာကို ပြောသူ ရပ်ပြီးမှ စတဲ့ နေရာတွေမှာပဲ လွတ်လပ်စွာ တိုင်းနိုင်ပါတယ်။ ဒီ source မှာ ဒီလို နေရာ **၉ ခု** ပဲ ရှိပါတယ်။
- ဒီ ၉ ခုထဲက caption ကတ်နဲ့ တွဲလို့ရတာ (ကတ်ရဲ့ ပထမ စကားလုံးမတိုင်ခင် ≥0.25s ကွာ + ±0.5s အတွင်း) **n = 3** ပဲ ရပါတယ်။
- Output audio ကနေ ရှာတော့ music bed ကြောင့် ၃ ခုပဲ တွေ့ပါတယ်။ ဒါကြောင့် source ကို သုံးထားပါတယ်။
- Source→output map: ~2–8s ကြားမှာ cut ၁ ခု ရှိပြီး အဲဒီနောက် lag **−0.14s** ပုံသေ ဖြစ်ပါတယ် (window corr 0.88–0.97)။ Pipeline log က "ဖြုတ် 0.18s" လို့ ပြောပါတယ်။ 0.04s ကွာတာက envelope resolution (10ms) × window ကြောင့် ဖြစ်နိုင်ပါတယ်။

## Layer 1: အဖြူ caption (ကတ် 72 ခု)

### offset ဖြန့်ဝေမှု

| offset | n | median | p5 | p95 | min | max | **a** (s) | **b** (s/s) |
|---|---|---|---|---|---|---|---|---|
| pipe_on − gemini_word | 71 | 0.000 | 0.000 | +0.020 | −0.170 | +0.080 | +0.0088 | −0.00026 |
| burn_on − pipe_on | 72 | −0.020 | −0.033 | +0.013 | −0.043 | +0.033 | −0.0081 | −0.00018 |
| burn_on − acoustic | **3** | +0.060 | −0.090 | +0.207 | −0.107 | +0.223 | +0.2238 | −0.00428 |
| pipe_on − acoustic | **3** | +0.070 | −0.092 | +0.223 | −0.110 | +0.240 | +0.2391 | −0.00448 |

- offset = caption_on − reference (+ = caption နောက်ကျ)။ Fit: `offset = a + b·t` (t = pipe_on s)။
- ⚠️ n = 3 ရဲ့ fit (a, b) က ကိန်းအရ အဓိပ္ပာယ် မရှိပါ (အချက် ၃ ချက်နဲ့ မျဉ်းတစ်ကြောင်း)။ တန်ဖိုးကိုသာ ပြထားပါတယ်။
- `burn_on − pipe_on` တန်ဖိုးတွေက **1/30s ပေါ်မှာ quantize ဖြစ်နေပါတယ်** (−0.033 · −0.017 · 0 · +0.013)။ ဒါက frame နယ်နိမိတ်ပါ။
- ground truth ၃ ခု (ကတ် · pipe_on · Gemini word · acoustic):
  - `c0024` 17.45 · word 17.43 · acoustic **17.21** → +0.22
  - `c0053` 39.63 · word 39.63 · acoustic **39.74** → −0.11
  - `c0070` 58.51 · word 58.49 · acoustic **58.44** → +0.06
- `pipe_on − gemini_word` ≠ 0 ဖြစ်တဲ့ ကတ်:
  - `c0004` +0.08
  - `c0089` −0.17 (graphic ဖျောက်ချိန် 73.79 ပြီးမှ ပြန်ပေါ်)
  - +0.02 ×9 (word timing ကို 0.01s rounding · concat 0.02s floor)

### ကတ် တစ်ခုချင်း (ဥပမာ အပိုင်း · ၇၂ ခုလုံးက `tm.mp4.timing_result.json`)

| ကတ် | pipe_on | pipe_off | gemini_word | burn_on | acoustic | pipe−word | burn−pipe | burn−acoustic |
|---|---|---|---|---|---|---|---|---|
| c0000 | 0.43 | 0.90 | 0.43 | 0.433 | — | 0.000 | +0.003 | — |
| c0004 | 2.55 | 3.17 | 2.47 | 2.533 | — | +0.080 | −0.017 | — |
| c0019 | 12.62 | 14.37 | 12.62 | 12.633 | — | 0.000 | +0.013 | — |
| c0024 | 17.45 | 17.80 | 17.43 | 17.433 | **17.21** | +0.020 | −0.017 | **+0.223** |
| c0043 | 29.00 | 30.73 | 29.00 | 28.967 | — | 0.000 | −0.033 | — |
| c0053 | 39.63 | 39.99 | 39.63 | 39.633 | **39.74** | 0.000 | +0.003 | **−0.107** |
| c0065 | 50.79 | 52.21 | (±0.3s အတွင်း မရှိ) | 50.767 | — | — | −0.023 | — |
| c0070 | 58.51 | 58.86 | 58.49 | 58.500 | **58.44** | +0.020 | −0.010 | **+0.060** |
| c0089 | 73.79 | 74.76 | 73.96 | 73.767 | — | −0.170 | −0.023 | — |
| c0091 | 75.56 | 77.51 | 75.56 | 75.533 | — | 0.000 | −0.027 | — |

- ဖျောက်ထားတဲ့ ကတ် (graphic ပေါ်ချိန်) က concat ထဲမှာ blank ဖြစ်ပြီး ဇယားထဲ မပါပါ။ Hide window ၅ ခု:
  - 30.73–33.93
  - 39.99–42.99
  - 48.19–50.79
  - 65.29–67.89
  - 70.99–73.79
- ⇒ ကတ် index ကွက်လပ် (c0003 · c0031 · c0044–47 …) တွေက ဒါကြောင့်ပါ။

## Layer 2: အဝါ overlay — **VOID** (gfx_size_16x9.json ဗလာဖြစ်ချိန် 14:11 နဲ့ render ထပ် · ~19:10 နောက်ပိုင်း ပြန်တိုင်းရန်)

~~(graphic · vplan 8 ခု → တပ်ရ 5 · no_room 3)~~ — အောက်ပါ ကိန်းအားလုံး ပယ်ဖျက်ပြီး၊ မှတ်တမ်းအဖြစ်သာ ချန်ထားသည်။

| tpl | text | plan_on | plan_off | burn_on | burn_off | burn_on−plan | burn_off−plan_off | detector ယုံလား |
|---|---|---|---|---|---|---|---|---|
| step_flow | အဓိကသော့ချက် ၃ ချက် | 30.73 | 33.93 | 30.767 | (34.90) | **+0.037** | (+0.97) ✗ | on ✓ · off ✗ (34.5s B-roll ထဲ အဝါရှပ်အင်္ကျီ) |
| fact_box | အေဂျင်စီကောင်း | 39.99 | 42.99 | 40.000 | 42.867 | **+0.010** | **−0.123** | ✓ |
| quote_block | N5 အောင်လက်မှတ် | 48.19 | 50.79 | 48.233 | 50.600 | **+0.043** | **−0.190** | ✓ |
| map_locator | သက္ခာလာနိုဘာဘာ | 65.29 | 67.89 | (64.27) | (68.87) | ✗ | ✗ | ✗ (ZIN APEX ဆိုင်းဘုတ် အဝါ) |
| subscribe_bug | Tokutei ဟုရေးပါ | 70.99 | 73.79 | (69.97) | (74.77) | ✗ | ✗ | ✗ (ဆိုင်းဘုတ် အဝါ) |

- ယုံလို့ရတဲ့ ကိန်းသာ: on-time n = 3 (+0.010 · +0.037 · +0.043) · off-time n = 2 (−0.123 · −0.190)။ Fit လုပ်ဖို့ မလုံလောက်ပါ။
- `plan_on − gemini_word` = **0.000** (5/5)။ Graphic `at` က Gemini word start ပေါ်မှာ တိတိ ကျပါတယ်။
- No_room နဲ့ မတပ်ရတဲ့ graphic: `side_bar` @0.43 · `chapter` @9.85 · `stat_title` @34.03
- ⚠️ ဒီ render (~14:0x–14:15) ပြေးနေတုန်း 14:11 မှာ shared `assets/gfx_size_16x9.json` က entry 593 → 4 ဖြစ်သွားပါတယ် (ကျွန်တော် မဟုတ်ပါ · `tools/gfxsize.py` subset run ဖြစ်နိုင်)။ `dress.py` က ဒီဖိုင်နဲ့ no_room ကို ဆုံးဖြတ်ပါတယ်။ ဒါကြောင့် no_room 3 ခုနဲ့ overlay n = 5 က ဒီအချက်ကြောင့် ညစ်ညမ်းနိုင်ပါတယ်။ Caption layer ကိန်းကိုတော့ မထိခိုက်ပါ။
- ⚠️ 33s: caption layer က `step_flow` (30.73–33.93) ကြောင့် **ဖျောက်** ထားပါတယ်။ Overlay layer ကတော့ ပေါ်နေပါတယ်။ Layer ၂ ခုရဲ့ အပြုအမူ ကွဲတာ ဒီနေရာမှာ ဖြစ်ပါတယ်။

## ffprobe

| | codec | start_time | time_base | r_frame_rate | nb_frames | duration | sample_rate |
|---|---|---|---|---|---|---|---|
| **output video** | h264 | 0.000000 | 1/15360 | 30/1 | 2326 (read 2326) | 77.533333 | — |
| **output audio** | aac | 0.000000 | 1/96000 | 0/0 | 7271 (read 7270) | 77.620312 | **96000** |
| source video | h264 | 0.000000 | 1/19200 | 60/1 | 4658 | 77.633333 | — |
| source audio | aac | 0.000000 | 1/44100 | 0/0 | 3346 | 77.693968 | 44100 |

- Output ရဲ့ video duration (77.533) နဲ့ audio duration (77.620) က **0.087s** ကွာပါတယ်။
- Output audio က **96 kHz** ပါ (source က 44.1 kHz)။



---

# ထပ်တိုး (Brief ②): music ပိတ် render + mux/resample ဖတ်ချက်

## သင်္ကေတ သဘောတူညီချက် (အတိအလင်း)

- **caption offset = caption_on − voice_onset** · **အပေါင်း = caption က အသံထက် နောက်ကျ**
- **lag = t_output − t_source** (အသံ/ရုပ် အကြောင်းအရာ တူတူအတွက်)။ အနုတ် = အဲဒီ အကြောင်းအရာက output မှာ source ထက် **စော** ရောက်တာ (cut က အချိန်ဖယ်လို့)
- ⇒ ယခင် report ရဲ့ **−0.14 က caption offset မဟုတ်ပါ**။ ဒါက source→output **lag** ဖြစ်ပြီး caption vs voice ကိန်း မဟုတ်ပါ။ Cut နောက်က source အကြောင်းအရာ အကုန်လုံးက output မှာ 0.14s စော ရောက်တာပါ။ Ground truth onset ကို output ပေါ် map လုပ်ဖို့ပဲ သုံးခဲ့ပါတယ်။
- ⚠️ ယခင်က "cut ~2–8s" လို့ ရေးခဲ့တာ **မှားပါတယ်**။ 10ms envelope window ရဲ့ t=2.0 ရလဒ်က r = 0.49 (ယုံလို့ မရ) ပါ။ 1ms waveform correlation နဲ့ ပြန်တိုင်းတော့ **t = 1.5s ကတည်းက lag −0.1437** ဖြစ်ပါတယ်။ ⇒ cut က ပထမ 1.5s အတွင်း ရှိပါတယ်။

## ① music ပိတ် render (`tm_nomusic.mp4`)

- `over={"music": None}` တစ်ခုတည်းပဲ ပြောင်းထားပါတယ်။ Seed = job id = `t_s916_pin` နဲ့ code (HEAD run.py copy) က `tm.mp4` နဲ့ တူပါတယ်။
- `ambience` knob က recipe မှာ **မရှိပါ** (`recipes.clean()` က ဖယ်ပါတယ်)။
- ASR (chunk 4 · လုံးရေ 2470/3008/2578/1781) နဲ့ cut (1 · 0.2s) က `tm.mp4` နဲ့ **တူပါတယ်**။
- SFX cue 12 ခု ကျန်ပါတယ် (log ထဲက အချိန်)။ ⇒ SFX ±0.2s အတွင်း onset ကို ဖယ်ပါတယ် (ဖယ်ခံရတာ 0 ခု)။

**တိုက်ရိုက် တိုင်းချက်: caption_on (concat) − output audio onset** (≥120ms တိတ် → +10dB · floor −31.3dB · ±0.5s အတွင်း တွဲ)

| n | median | p5 | p95 | min | max | a (s) | b (s/s) |
|---|---|---|---|---|---|---|---|
| **7** (onset 10 ခုထဲက) | **+0.030** | −0.128 | +0.236 | −0.140 | +0.290 | +0.1519 | −0.0033 |

| voice onset | caption on | offset |
|---|---|---|
| 2.26 | 2.55 | +0.290 |
| 11.91 | 12.02 | +0.110 |
| 28.14 | 28.00 | −0.140 |
| 39.73 | 39.63 | −0.100 |
| 43.13 | 43.16 | +0.030 |
| 58.44 | 58.51 | +0.070 |
| 59.96 | 59.96 | 0.000 |

- ⚠️ ပြောသူက ဆက်တိုက် ပြောလို့ ≥120ms ရပ်ချက် **onset 10 ခုပဲ** ရှိပါတယ်။ ၉ ခုထက် များလာပေမယ့် n = 7 ပဲ ရပါတယ်။

## A/V lag (အသံ vs ရုပ် · source → output)

| t_out | audio lag (1ms · r) | video lag (1/60s · corr) |
|---|---|---|
| 1.5 | −0.1437 (0.815) | (+0.183 · 0.820 ✗ graphic) |
| 5.2 | −0.1437 (0.953) | −0.133 (0.987) |
| 9.5 | −0.1437 (0.938) | −0.100 (0.992) |
| 17.0 | −0.1437 (0.960) | −0.100 (0.986) |
| 26.3 | −0.1437 (0.960) | −0.133 (0.988) |
| 37.0 | −0.1437 (0.959) | −0.133 (0.972) |
| 45.2 | −0.1437 (0.963) | −0.133 (0.977) |
| 51.0 | −0.1437 (0.946) | −0.117 (0.983) |
| 58.0 | −0.1437 (0.937) | −0.133 (0.967) |
| 63.0 | −0.1437 (0.930) | −0.083 (0.983) |
| 69.5 | −0.1437 (0.957) | −0.150 (0.971) |
| 75.5 | −0.1437 (0.963) | −0.133 (0.977) |

- Audio lag: 12/12 နေရာမှာ **−0.1437 ပုံသေ** ပါ (b = 0)။ Video lag (corr ≥0.95 · n = 11): median **−0.133** · range −0.083 ~ −0.150 ပါ။ ±1–3 source frame (1/60s) ကွာတာက output 30fps frame နဲ့ 60fps source frame ကို ကိုက်တဲ့ ambiguity ပါ။
- `tm.mp4` ရဲ့ video lag (corr ≥0.95 · n = 22): median −0.117 · a −0.1019 · b −0.00029
- **video lag − audio lag = −0.133 − (−0.1437) = +0.011s** (median ချင်း)
- Pipeline log က "ဖြုတ် 0.18s" လို့ ပြောပါတယ်။ တိုင်းထားတဲ့ shift က 0.1437s ပါ။ ကွာတာ 0.036s ပါ။

## ② mux / resample ဖတ်ချက် (render မလို)

**1. Audio/video ကို ထိတဲ့ ffmpeg command (HEAD `worker/run.py` · `core/spans.py` · `core/music.py` · `core/dress.py`)**

| အဆင့် | command (အဓိက option) |
|---|---|
| span ဖြတ် | `ffmpeg -ss a -i src -t d -af afade=in…,afade=out… [-vf crop/scale punch] -r 30 <h264> -c:a aac -b:a 192k -avoid_negative_ts make_zero sNNNN.mp4` |
| span ဆက် | `ffmpeg -f concat -safe 0 -i parts.txt -c copy cut.mp4` |
| zoom (`_breathe`) | `-vf crop…,zoompan… -r 30 -c:v libx264 … -c:a copy` |
| compose | overlay input တိုင်း `-itsoffset <at> -i <mov/png>` (video · `overlay=…:shortest=0:repeatlast=0`)。 audio က input 0 ကနေ |
| music bed | `amix=inputs=2:duration=first:normalize=0` (+ sidechaincompress) · `-c:v copy -c:a aac 192k` |
| SFX | `adelay=<ms>|<ms>` + `amix=…:normalize=0:dropout_transition=0` |
| mastering | `-af loudnorm=…:linear=true,alimiter=… -c:v copy -c:a aac -b:a 192k -movflags +faststart` |

- `-async` **မရှိပါ** · `-shortest` **မရှိပါ** (overlay ရဲ့ `shortest=0` သာ)
- `aresample` က short-916 လမ်းကြောင်းမှာ **မရှိပါ** (run.py:4279 က multi-take join လမ်းကြောင်းပဲ)
- `-itsoffset` ကို overlay **video** input တွေအတွက်ပဲ သုံးပါတယ်

**2. 44.1 kHz → 96 kHz:**
- Mastering ရဲ့ `loudnorm` filter က ဖြစ်စေတာပါ။ Final command မှာ `-ar` မပါပါ။
- စမ်းသပ်ချက်: 44.1 kHz sine → `loudnorm` (dynamic ရော `linear=true` ရော) → aac ⇒ **96000 Hz** ထွက်ပါတယ်။
- ⇒ ရွေးချယ်ထားတာ မဟုတ်ပါ၊ ffmpeg default ပါ (loudnorm က 192k ထုတ် → AAC ရဲ့ အမြင့်ဆုံး 96k)။

**3. 60 → 30 fps:**
- `-r 30` က span cut / `_breathe` / overlay render ရဲ့ **video output option** ပဲ ဖြစ်ပါတယ်။ Audio က `-c:a aac` / `copy` နဲ့ သီးသန့် သွားပါတယ်။
- အတည်ပြုချက်: audio lag က 1.5–75.5s တစ်လျှောက် −0.1437 ပုံသေ ဖြစ်ပါတယ် (b = 0) ⇒ audio ကို ပြန်ချိန်တာ မရှိပါ။

**4. audio က video ထက် 0.087s ရှည်တာ:**

| | video | audio | audio − video |
|---|---|---|---|
| source | 77.633 | 77.694 | **+0.061** |
| output | 77.533 | 77.620 | **+0.087** |

- Start: stream ၂ ခုလုံး `start_time` 0.000 ပါ။ 1.5s မှာ audio lag −0.1437 · video lag (corr ≥0.95 ဖြစ်တဲ့ ပထမ နေရာ 5.2s) −0.133 ⇒ start မှာ သိသာတဲ့ ကွာခြားမှု မရှိပါ။
- ⇒ 0.087 ထဲက **0.061 က source ကနေ လာပါတယ်**။ Pipeline က ထပ်တိုးတာ **+0.026s** ပါ (30fps frame 1 ခု အောက်)။ Duration ကွာခြားမှုက အဆုံးဘက်မှာ ရှိပါတယ်။

## Layer 2 overlay

**VOID** (အထက်တွင်)。 ~19:10 gfx_size ပြည့်ပြီးမှ ပြန်တိုင်းပါမယ်။

— ဒီမှာ ရပ်ပါတယ်။ နောက်တစ်ဆင့်က stroke Step A (`cap_base` 0.805 တစ်ခုတည်း)။ Commit မလုပ်ခင် ကြေညာပါမယ် (R-G2)。
