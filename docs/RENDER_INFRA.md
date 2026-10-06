# Render infrastructure — user ၁၀၀၀ အတွက် (roadmap ⑤ · ၂၀၂၆-၁၀-၀၇)

> ⚠️ ဈေးနှုန်းများ **ခန့်မှန်း**ချက်သာ — အကောင့် မဖွင့်ရသေး (ဖွင့်ခြင်းက Zin ဆုံးဖြတ်ချက်)။ မဖွင့်ခင် AWS /
> Remotion / Hetzner ရဲ့ လက်ရှိ ဈေးစာရင်းကို ပြန်စစ်ပါ။

## တိုင်းထားသော အခြေခံ (Mac · ၂၀၂၆-၁၀-၀၇)

| | တိုင်းချက် |
|---|---|
| 60s ဗီဒီယို · beat ၇ ခု (graphic frame ~25s) | Remotion window render + overlay + SFX mix **~150s** |
| QC ပြင်ပြီး ပြန်ဆောက် (window ၁ ခုသာ ပြောင်း) | cache ကြောင့် ~30s ထပ် |
| ဗီဒီယို တစ်ခုလုံး Remotion render (မသုံးတော့) | ~19 မိနစ် ⇒ window render က **~8× မြန်** |

## ရွေးချယ်စရာ ၃ ခု

### A. Mac worker တစ်လုံးတည်း (ယခု)
* ကုန်ကျ ≈ ၀ · throughput ≈ ၂၀ ဗီဒီယို/နာရီ (beat ပိုင်းသာ) — IKKI ကျန်အဆင့် (ASR · cut · B-roll · grade) ပါ
  ပေါင်းလျှင် တစ်နာရီ ~၄–၆ ပုဒ်။ user ၁၀၀၀ × တစ်လ ၄ ပုဒ် = ၄၀၀၀ ⇒ **မလောက်** (~၇၀၀–၁၀၀၀ worker-hour)။

### B. Remotion Lambda (AWS)
* beat window တစ်ခုကို Lambda အများ ခွဲ render ⇒ ဗီဒီယို တစ်ပုဒ် beat ပိုင်း **~၁၅–၃၀s**။
* ကုန်ကျ (ခန့်မှန်း): frame ~750/ဗီဒီယို · 2GB Lambda · ~300 GB-s ⇒ **~$0.005–0.01/ဗီဒီယို** + S3/egress။
* Remotion license (company): Automators — render တစ်ခု $0.01 · လ အနည်းဆုံး $100 (ယခင် စစ်ချက်)။
* ၄၀၀၀ ပုဒ်/လ ⇒ Lambda ~$40 + license $100 ≈ **$140/လ**။
* ⚠️ IKKI ကျန်အဆင့် (ffmpeg grade/B-roll/ASR) က Lambda မဟုတ် ⇒ worker farm ဆက်လို။

### C. Render farm (Hetzner/VPS CPU box · Docker worker)
* `worker/run.py` + `~/ikki-remotion` (Chrome headless) ကို Docker image တစ်ခုတည်း ⇒ box N လုံး queue ယူ။
* 8 vCPU box ≈ Mac ၀.၆–၀.၈ ဆ ⇒ box ၄–၆ လုံး (peak အတွက် autoscale) ≈ **€250–400/လ**။
* macOS Vision (posecheck) မရ ⇒ Linux မှာ MediaPipe face detector အစားထိုး လို (beatqc.faces)။

## အကြံပြု (အဆင့်လိုက်)

1. **ယခု → user ၁၀၀**: Mac + VPS worker ၁ လုံး (C ရဲ့ အစ) · beats ကို worker ထဲမှာပဲ render။
2. **user ၁၀၀ → ၁၀၀၀**: C farm (Docker) + beat render ကို B (Lambda) သို့ ခွဲ ⇒ worker CPU ကို IKKI အဆင့်များအတွက် ထား။
3. queue: ယခု `/api/w/claim` pull model ဆက်သုံး · worker label (`mac` · `linux-gpu` · `lambda`) ထည့် ⇒ job အလိုက် ပို့။
4. ကုန်ကျ စောင့်ကြည့်: `REPORT["beats"]` (render s · window · QC fix) ကို usage dashboard ထဲ ထည့်။

## Lambda စတင်ရန် (Zin က အကောင့် ဖွင့်ပြီးမှ)

```bash
cd ~/ikki-remotion
npm i @remotion/lambda@4.0.300
npx remotion lambda policies role      # IAM role (AWS console မှာ Zin ကိုယ်တိုင်)
npx remotion lambda functions deploy --memory=2048 --timeout=240
npx remotion lambda sites create src/index.ts --site-name=ikki-beats
```
ပြီးလျှင် `core/remo.py::_build_beats` ထဲ `npx remotion render` ကို `renderMediaOnLambda` (Node helper) နဲ့ အစားထိုး —
interface (`beats_props.json` · `--frames`) မပြောင်း။
