# Caption on speech runs — ③ render + ဂိတ် ၈ ခု (2026-09-27)

Recipe `short-916` + `cap_timing="speech"` · seed = job id = `t_s916_pin` · harness (IKKI ကုဒ် wrap ပဲ) · **commit မလုပ်ရသေး (R-G2)**
ကိန်းအားလုံး ffmpeg ကို ပို့တဲ့ concat list (burn-in နဲ့ ±1 frame · ယခင်တိုင်းထား n=72) ပေါ်က · n = ကတ်အားလုံး

## Render ၃ ကြိမ် — တစ်ကြိမ် တစ်ပြောင်းလဲမှု

| render | ပြောင်းတာ | G1 on | G2 off | G3 | G4 | G5 | G6 | G7 | G8 |
|---|---|---|---|---|---|---|---|---|---|
| ① speech.mp4 | speech cards (spec) | ✗ med −80 ms · p95 120 | ✗ med −80 · p95 120 | ✗ 5 | ✓ 0 | ✗ 3 | ✓ 0 | ✗ | ✓ |
| ② speech2.mp4 | + concat clock fix | ✓ 0 · 0 | ✓ 0 · 49 ms | ✓ 0 | ✓ 0 | ✗ 2 | ✓ 0 | ✗ | ✓ |
| **③ speech3.mp4** | + ကတ် အတိုဆုံး 0.30 s | **✓ 0 · 0** | **✓ 0 · 49 ms** | **✓ 0** | **✓ 0** | **✓ 0** | **✓ 0** | **✗ 3** | **✓** |

(G1/G2 = median · p95 · limit 33 / 66 ms)

## ③ အသေးစိတ်

- speech run 32 → ကတ် 98 · ပြ 83 · graphic ပေါ်ချိန် ဖျောက် 15 (G5 ပျောက်ကတ် မဟုတ် · ယခင်အတိုင်း)
- G1 n = 23 (run စတဲ့ ကတ်) · G2 n = 23 (run ဆုံးတဲ့ ကတ်) · ကျန်ကတ်တွေက run အတွင်း စကားလုံးကြား ခွဲမှတ်မှာ ပြောင်း (ကတ်→ကတ် · ဗလာ မရှိ)
- on/off ≠ ရည်ရွယ်ချိန် ±1 frame: 9 ကတ် · 7 ခုက graphic ပေါ်လို့ ဖြတ် (ရည်ရွယ်ချက်) · 2 ခုက ≤40 ms gap ကို ယခင်ကတ် ဆက်ကိုင် (G4 100 ms အတွင်း)
- G7: ကြာချိန် max 1.98 s (≤4.0 ✓) · mid-word split 0 ✓ · **အကျယ် > 778 px: 3 ကတ်** (max 1263 px)
- G8: ကတ် 4672 byte ≤ ASR 4764 byte ✓
- ဗလာ flash (run ကြား gap မှာ ပျောက်ပြီး ပြန်ပေါ်): 23 ခု / 77.6 s — spec အတိုင်း

## တွေ့ပြီး ပြင်ခဲ့တဲ့ ချို့ယွင်းချက် ၂ ခု (caption path · ကျွန်တော့ ပိုင်)

1. **concat clock** (`captions.track` → `concat_items`): gap ≤ 40 ms ကို blank မထည့်ဘဲ နောက်ကတ်ကို ချက်ချင်း စ၊ ကြာချိန်က `b−a` ပဲ ⇒ gap တိုင်း running time ထဲက ပျောက်ပြီး နောက်ကတ်အားလုံး စော (① median −80 ms · max −120 · 56/81 ကတ် > 1 frame)။ ကတ် drop ဖြစ်ရင် blank ကို နှစ်ခါ ရေတာလည်း ပါ။ ⇒ ယခင်ကတ်က gap ကို ကိုင်ထား (≤40 ms)၊ running sum = အချိန်အမှန်။ ① ရဲ့ ကတ်တွေနဲ့ offline replay: median −0.080 → **0.000** · >1 frame 56 → **0**။ word-timing style အားလုံးကိုပါ သက်ရောက် (ပိုမှန်လာ)။
2. **sliver ကတ်** (`speech_cards`): run ရှည်ကို ခွဲမှတ် တစ်ခုချင်း သီးခြား ရှာလို့ Gemini word အချိန် စုနေရင် (17.43 မှာ ၂ လုံး) ခွဲမှတ် ၂ ခု 40 ms ကွာ ⇒ 0.04 s / 0.00 s ကတ် ⇒ track က drop (G5)။ ⇒ ခွဲမှတ်ကို အစဉ်လိုက်၊ ကတ်တိုင်း ≥ **0.30 s** (render မလုပ်ခင် သတ်မှတ်)၊ နေရာ မလောက်ရင် စကားလုံးကို ယခင်ကတ်ထဲ ပေါင် (မဖျက်)။ ③ min 0.30 s ✓။

Test: `test_concat_clock.py` (4) · `test_speech_cards.py` (+1 = 7) · caption test 17/17 ✓ · script-style test 19 ဖိုင် ✓ (upload_resume ကျ 5 · unittest `test_tplvar` ကျ 2 — caption နဲ့ မဆိုင် · import မလုပ် · TH ရဲ့ uncommitted `gfxcat.py` ဖြစ်နိုင်)

## ဆုံးဖြတ်ရန် (Z4)

1. **G7 ✗ — 778 px ကျော် 3 ကတ်**: Gemini က နေရာလွတ်မပါတဲ့ စကားစု တစ်ခုလုံးကို "စကားလုံး ၁ လုံး" အဖြစ် ပေး (ဥပမာ 34 လုံးသား `ကိုယ့်ခြေထောက်ပေါ်ကိုယ်…အတွက်`)။ font 60% (80→47 px) အထိ ချုံ့လည်း 1263 / 817 / 812 px။
   - (a) Burmese syllable နယ်နိမိတ်မှာ ခွဲ (စာလုံး မပြောင်း · ဒါပေမယ့် "mid-word" ဖြစ်နိုင်)
   - (b) shrink floor ကို ထပ်ချ (1263 px ဆို ~29 px · ဖတ်မရ)
   - (c) ဒီအတိုင်း လက်ခံ (98 ကတ်မှာ 3 · frame ထဲ ဝင်ပေမယ့် TikTok right rail ထိ)
2. **`track` ရဲ့ hide step bug (မပြင်ရသေး)**: `y−x > 0.20` ကို graphic မထိတဲ့ ကတ်ပါ စစ်လို့ 0.12–0.20 s ကတ် graphic မရှိဘဲ ပျောက်။ skip report ရဲ့ "DROPPED" ၃ ခုထဲက 0.17 s ၂ ခု ဒါပါ။ short-916 speech path မှာ ကတ် ≥0.30 မို့ မထိ · word-timing style တွေမှာ ထိ ⇒ ပြင်ရင် style တခြားတွေ output ပြောင်း ⇒ ခွင့်ပြုချက်လို။
3. ဗလာ flash 23 ခု (spec အတိုင်း ထား)။

## နောက်တစ်ဆင့်

- stroke ဂိတ် ၅ ခု (y · face · band · stroke÷text · edge) ကို speech3 ပေါ် သီးခြား ပြန်တိုင်း
- commit: R-G2 ကြေညာ ပြီးမှ
