# Cut Engine — စစ်ဆေးချက် နှင့် ပြန်လည် ဒီဇိုင်း

> ⚠️ **Phase 0 စည်းမျဉ်း** — 「Do not replace the old engine blindly」。
> ဤစာတမ်းက **ကုဒ် မပြင်ခင်** စစ်ဆေးချက်。 ငြင်းချက်တိုင်းကို ဖိုင်:လိုင်း
> ဒါမှမဟုတ် တိုင်းချက်နဲ့ အတည်ပြု/ငြင်းထားသည်。 (၂၀၂၆-၀၉-၂၁)

## ၁ · ပြောထားသော ချို့ယွင်းချက် ၇ ခု — စစ်ဆေးချက်

| # | ငြင်းချက် | ရလဒ် | သက်သေ |
|---|---|---|---|
| ၁ | `_place()` က `words` ဖျောက်သည် | **အတည်** | `asr.py:616` မှာ ဖတ်ပြီး span တွက်သည် · `asr.py:670,685` ရဲ့ output မှာ `text/start/end` သာ |
| ၂ | speech detection က global energy + band heuristic | **တစ်ပိုင်း** | `measure.py:117` `thr_of()` က **ဖိုင်တစ်ခုချင်း** ချိန်သည် (p95−20, p10+7) — ကိန်းသေ မဟုတ်။ သို့သော် **ဖိုင်တစ်ခုလုံးအတွက် တစ်ခုတည်း** · frame probability မရှိ · hysteresis မရှိ · neural VAD မရှိ |
| ၃ | cough က heuristic သာ | **အတည်** | `clean.py:43` — 3500–7800 Hz ပေါက်ကွဲမှု · median +25 dB · ၀.၀၆–၀.၈၀s。 အမျိုးအစား ခွဲခြားမှု မရှိ |
| ၄ | repeat က whitespace token | **အတည်** | `clean.py:114` `s["text"].split()`。 (`_grams()` က character n-gram သုံးသည် — retake အတွက်သာ) |
| ၅ | ဖြတ်မှတ်ကို speech probability နဲ့ အမှတ် မပေး | **တစ်ပိုင်း** | `cut.py:subtract()` မှာ `quiet_at()` (စွမ်းအင် အနိမ့်ဆုံးမှတ်) ရှိသည် — probability မဟုတ် · scoring function မရှိ · safety margin မရှိ |
| ၆ | `_drop_exact` ကို server ဘက် မစစ် | **အတည်** | `run.py:756` — `CUT.subtract(spans, user_drop_exact, None, snap=0.0)` ⇒ `sil=None` · `snap=0` ⇒ `edges` ဗလာ · `quiet_at` မလုပ် ⇒ **နယ်နိမိတ် အတိအတိုင်း ဖြတ်**သည်。 source range စစ်ချက်လည်း မရှိ |
| ၇ | review က တိတ်တဆိတ် ဖျက်မှု မဖြစ်စေရ | **တစ်ပိုင်း** | `clean.plan()` — repeat/restart က `flags` (ပြရုံ) ✓ · **cough နှင့် filler က `auto`** ⇒ တိုက်ရိုက် ဖြတ်သည် ✗ |

### ⚠️ ငြင်းချက် ၂ အတွက် တိုင်းချက်

`tokutei.mp4` (၇၇.၇s) မှာ ၁၀s ဝင်းဒိုးအလိုက် threshold က **၃.၇ dB သာ** ကွာပြီး
speech map က **၁.၄% (၁.၁၂s)** သာ ပြောင်းသည် ⇒ ဤ footage မှာ single-threshold
က **အဓိက ပြဿနာ မဟုတ်**ပါ。 ဆူညံမှု ပြောင်းလဲသော footage မှာ ပြဿနာ ဖြစ်မည် —
ဒါကို **သက်သေ မရှိသေး** ⇒ benchmark fixture လိုသည် (Phase 0)。

### ⚠️ ပိုအရေးကြီးသော တွေ့ချက် (ငြင်းချက်ထဲ မပါ)

report ၁၁ ခု စစ်ချက် — **job ၆/၁၁ မှာ ဝါကျ ၈၅–၉၆% က bias fallback** ဖြစ်သည်
(တိတ်ဆိတ်မှုနဲ့ အတည်ပြု၍ မရ)。 ခေတ္တရပ် မရှိသော footage မှာ silence-based
anchor က **လုံးဝ မကူညီ**ပါ ⇒ forced alignment မရှိဘဲ word-level တိကျမှု
မရနိုင်ပါ (Phase 1 ရဲ့ အဓိက အချက်)。

```
bias fallback   snap ရနိုင်     footage
   5.0%         19/20          ခေတ္တရပ် ရှိ
  25.5%         38/51
  29.1%         39/55
─────────────────────────────
  84.6%          4/26          ခေတ္တရပ် မရှိ
  94.1%          1/17
  96.0%          1/25
```

## ၂ · Canonical Timeline Model

ယခု **မော်ဒယ် မရှိ**ပါ — `spans` (tuple စာရင်း) · `segs` (dict စာရင်း) ·
`sil`/`sp` (tuple စာရင်း) · `flags` · `plan` dict တို့ သီးသန့်စီ ရှိပြီး
module တစ်ခုချင်း ကိုယ်ပိုင် ပုံစံနဲ့ ပြန်တွက်သည်。

⇒ `core/timeline.py` — **တစ်ခုတည်းသော အမှန်**

```python
Timeline
  src_dur, sample_rate, frame_hz
  speech_prob[]        # frame တစ်ခုချင်း ၀–၁ (bool မဟုတ်)
  noise_floor[], snr[]
  speech[], silence[]  # confidence နှင့်
  segments[]           # transcript + timing_confidence
  tokens[]             # word/token + timing + confidence
  events[]             # sound-event candidate + label + confidence
  candidates[]         # filler / repeat / retake / silence
  cuts[]               # အောက်က ပုံစံအတိုင်း
  decisions[]          # user accept/reject + reason
  trace[]              # ဘာကြောင့် လက်ခံ/ပယ်/ရွှေ့/ပိတ် — အကုန်
```

ဖြတ်ချက် တစ်ခုချင်း —

```json
{ "id": "", "type": "silence|filler|cough|repeat|retake|user",
  "source_start": 0, "source_end": 0,
  "safe_start": 0, "safe_end": 0,
  "confidence": 0.0, "reasons": [],
  "speech_probability_at_edges": [0.0, 0.0],
  "local_snr": 0.0, "transcript_token_ids": [],
  "proposed_by": "", "requires_review": true,
  "user_decision": null, "rejection_reason": null }
```

## ၃ · ယုံကြည်မှု အဆင့် ၃ ဆင့်

| အဆင့် | ဘာတွေ | ယခု အခြေအနေ |
|---|---|---|
| **A · အလိုအလျောက်** | အတည်ပြုပြီး ရှည်သော တိတ်ဆိတ်မှု | ✓ ရှိပြီး (`cut.plan`) |
| **B · review** | filler · cough · repeat · retake · မသေချာသော အချိန်မှတ် | ⚠️ repeat/retake ✓ · **cough/filler က auto ဖြစ်နေ** |
| **C · ဘယ်တော့မှ auto မဖြတ်** | စကားနဲ့ ထပ်သော cough · alignment မသေချာ · semantic repeat · speaker ထပ် | ⚠️ cough က စကားထဲဆို ကျော်သည် (`measure.sounds`) · ကျန်တာ မစစ်ရသေး |

## ၄ · အဆင့်လိုက် အစီအစဉ်

- **Phase 0** — အပြောင်းအလဲ မလုပ်ဘဲ တိုင်းတာမှု ထည့်、adapter、benchmark fixture
- **Phase 1** — `words` ကို ထိန်းသိမ်း + စစ်ဆေး + confidence · **forced alignment
  မရှိလျှင် segment-level ဟု ရိုးရိုးသားသား ပြောရမည်**
- **Phase 2** — speech probability ensemble
- **Phase 3** — candidate ↔ auto-removal ခွဲခြား
- **Phase 4** — boundary scoring + render safety
- **Phase 5** — Script Editor (waveform · audition · nudge)

## ၅ · ကတိ မပေးနိုင်သေးသည့် အချက်များ

- **Burmese forced alignment** — MMS_FA ကို ၂၀၂၆-၀၉-၁၈ စမ်းပြီး
  **နယ်နိမိတ် ၆ ခုမှ ၅ ခု စကား run ထဲ ကျ**ခဲ့သည် (`measure.py:158`) ⇒
  ဖြတ်၍ မရပါ。 အစားထိုး aligner ကို **မြန်မာ အသံနဲ့ တိုင်းပြီးမှ** ဖွင့်ရမည်。
- **labelled benchmark မရှိသေး** ⇒ precision/recall ကိန်း **မပြောနိုင်သေး**。
- ⇒ ဤစာတမ်းထဲ 「၁၀၀% တိကျ」ဆိုသော ကတိ **မပါပါ**。
