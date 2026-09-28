# short-916 စာလုံးပေါင်း မှား — ASR တိုင်းတာ (2026-09-28)

Zin: check20 NEW ပြီး 「အချိန်ကတော့ ကိုက်ပြီ · စာလုံးပေါင်းတွေ လွဲနေပါသေးတယ်」
(ယခင် check20 ✗ ၁၅ ခု = **အချိန်** မကိုက် — Zin အတည်ပြု)。

⛔ pipeline ASR model မပြောင်း · asr.py မပြင် — scratch ထဲ monkeypatch နဲ့သာ တိုင်းသည်。
Model = `gemini-3.1-flash-lite` (pipeline အတိုင်း) · အသံ `tokutei.mp4` · chunk တူ。

## ၁. တကယ် မှားနေတာ (script + 3.8-flash နှစ်ခုလုံးက pipeline နဲ့ မတူ · တစ်ခုတည်း အမှန်ကို ပြ)

| pipeline | အမှန် (ပြောတာ) |
|---|---|
| ဗီဇာနဲ့ လုပ်လုပ်ချင် | ဗီဇာနဲ့ **အ**လုပ်လုပ်ချင် |
| တောင်းလို့ပုံတွေမှာ | တောင်လိုပုံနေမှာ |
| တစ်ခုတည်းအတွက် | Tokutei အတွက် |
| ကျောင်းနံနက်တက်ရတဲ့ | ကျောင်း ၂ နှစ်တက်ရတဲ့ |
| တိုက်ရိုက်လုပ်သက်ဝင်တဲ့ | တိုက်ရိုက် အလုပ်တန်းဝင်တဲ့ |
| သက္ခာလာနိုဘာဘာ | Takadanobaba |
| ဇယားအပတ်မှာက | J-Path မှာက |
| ကျွန်တော်တို့ရဲ့ ဒီနေရာ | ကျောင်းရဲ့ တည်နေရာ (ပြောသူ အမျိုးသမီး) |
| လက်မလွတ် | လက်မလွှတ် |
| ပရိုဂရမ် | Program |

⚠️ 3.8-flash ကိုယ်တိုင် ground truth မဟုတ် · ဤ ၁၀ ခုက script ပါ သဘောတူသော နေရာသာ。
⚠️ script ≠ ပြောတာ (script 「၄ နှစ်」 · ပြော 「၂ နှစ်」 · script 「Zin Apex」 · ပြော 「J-Path」) ⇒ script ကို စာတန်းအဖြစ် တိုက်ရိုက် မသုံးနိုင်。

## ၂. A/B (run ၂ ခုစီ)

| arm | အမှန် /10 | script ကူးထည့် (မပြောတာ) /5 | 3.8 နဲ့ သဘောတူ |
|---|---|---|---|
| pipeline insp2 (ယခင် run) | 0 | 0 | 92.2% |
| base (prompt မပြောင်း) | 3 · 3 | 0 · 0 | 92.1 · 91.7% |
| **terms** (script ထဲက Latin/နာမည် စာရင်းသာ) | **4 · 4** | **0 · 0** | 92.8 · 92.8% |
| **script** (script အပြည့် လမ်းညွှန်) | **7 · 8** | **2 · 2** 🔴 | 87.4 · 86.2% |

- 🔴 script arm က run ၂ ခုလုံး **「J-Path」 နေရာမှာ 「Zin Apex」** ရေး — company နာမည် မှား ⇒ customer မှာ လက်မခံနိုင်。 「သက်သာစွာနဲ့」 (မပြော) လည်း ထည့်。
- terms arm: ဘေးကင်း ဒါပေမယ့် +1 သာ — 「Takadanobaba」 စာရင်းထဲ ပါလျက် မှားရေး ⇒ **model ရဲ့ နား**က ကန့်သတ်ချက်。
- base 0 (insp2) vs 3 (ယခု) — run အကြား ကွဲပြားမှု ကြီး (n=2 · အချက်ပြ သက်သက်)。

## ၃. model — အလုပ်လုပ်တာ flash-lite တစ်ခုတည်း

- `gemini-3.8-flash`: chunk ၄ ခု ဆက်တိုက် အလွတ် (quota) — ယခင် 429 အတိုင်း
- `gemini-flash-latest`: chunk ၃/၄ အလွတ်
- logprobs: model ၃ ခုလုံး 400 (ယခင် တိုင်း)

## ၄. ⇒ ဆုံးဖြတ်ရန်

1. **terms (ဘေးကင်း · +1)** — job မှာ script ပါမှ script ထဲက Latin/နာမည် စာရင်းကို ASR ထဲ ထည့် (ပါမလာရင် ယခုအတိုင်း)
2. **script (+5 · company နာမည် မှားနိုင်)** — ကာကွယ်ချက်ကို အသံ မပါဘဲ ဆောက်လို့ မရ (J-Path↔Zin Apex ကို စာသားနဲ့ ခွဲမရ)
3. **လူ ပြင်** — IKKI transcript editor မှာ မသေချာသော စကားလုံးကို အမှတ်ပြ (base run ၂ ခု / terms arm မတူရာ) → user က ပြင် → `align_provided` နဲ့ ပြန်ညှိ (ရှိပြီးသား လမ်း)
4. **model ပိုကောင်း** — 3.8-flash quota (paid key) ရမှ · coordinator ခွင့်ပြုချက်

ဖိုင်: `scratchpad/s916/asr_script_ab.py` · `ab_*.json`

## ၅. ⚠️ approve က `words` ဖယ် ⇒ short-916 စာတန်း ၀ (တွေ့ပြီး ပြင်ပြီး)

- `approve` / `reedit` က ကျန်တဲ့ဝါကျကို `dict(text, start, end)` ပဲ ဆောက် ⇒ **`words` ပျောက်** (dev DB: 19/19)
- `align_provided` က `words` ပြန်မဆောက် (0/19) ⇒ worker ရဲ့ word pop က **ကတ် ၀** · `cards_pre=[]` ⇒ track က
  「`is not None`」 စစ်သဖြင့် **စာတန်း လုံးဝ မပါသော ဗီဒီယို** — review → approve လမ်းကြောင်း short-916 job တိုင်း
- `fix` က `text` ကိုပဲ ပြောင်း · `words` မပြောင်း ⇒ word pop မှာ user ✓ ပြင်ချက် **မပေါ်**
- ပြင်ချက်:
  1. API (approve · reedit) — စာကြောင်း မပြောင်းလျှင် မူရင်း `words` ဆက်ထည့်
  2. worker — `fix` ရှိလျှင် `scriptfix.retext()` နဲ့ `words` ရဲ့ စာသားကို fix အတိုင်း (အချိန် မပြောင်း)
  3. worker — word pop / speech timing ကတ် ၀ ⇒ ဝါကျ အချိန် စာတန်းသို့ ပြန်ကျ (စာတန်း မပျောက်စေ)
- စစ်ချက် (render မပါ · worker လမ်း simulate): fix ပါ ⇒ ကတ် 115 · 「Takadanobaba」 ကတ်ပေါ် ✓ · words မပါ ⇒ ကတ် 0 (ယခင်) → fallback
- ✅ **render အပြည့်နဲ့ စစ်ပြီး** (`fix1` · approve လမ်း = `job.segs` + fix ၄ ခု · Zin 「renderလုပ်ပေးပါ」):
  word pop ကတ် 112 (0 မဟုတ်) · 「Tokutei အတွက်」18.4s · 「လက်မလွှတ်」69.7s · 「ဒီ Program နဲ့」71.0s frame ပေါ် ✓ ·
  「Takadanobaba」ကတ် (65.9s) က location graphic ဖုံး ⇒ ဖျောက် (graphic ကိုယ်တိုင် Takadanobaba ပြ) ·
  G1–G9 ✓ · QC ✓ (−14.1 LUFS · TP −1.8) · deploy မလုပ်ရသေး
  ⚠️ ကတ် <0.25s 14% (insp2 8%) — ASR run မတူ (base_1 words) ⇒ run ကွဲပြားမှု · ပြင်ချက်ကြောင့် မဟုတ်
