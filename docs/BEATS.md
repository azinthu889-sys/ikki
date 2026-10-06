# IKKI Beats — စကားလုံးလိုက် infographic စနစ် (၂၀၂၆-၁၀-၀၇)

Zin ရဲ့ roadmap ၇ ဆင့် (AI Director · library · brand kit · timing+SFX · render infra · auto QC · editor UX) ကို
ဒီစာမျက်နှာက စုပေးထားပါတယ်။ **Registry တစ်ခုတည်း**ကနေ အားလုံး ထွက်ပါတယ်။

```
transcript (MMS word time · o0)
   │  core/director.py  ── Gemini (gemguard cache) ──┐
   │                     └─ rules (ဂဏန်း·ငွေ·ရက်စွဲ·brand·မြို့·စာရင်း·မေးခွန်း·သတိ·CTA)
   ▼
beats JSON  [{type, at, dur, pos, variant, ...params}]   ← registry schema နဲ့ validate
   │  core/remo.py · compose_beats   (beat ဝင်းဒိုးသာ Remotion render · ffmpeg overlay)
   │  SFX = registry `sfx` + တိုင်းထားသော `hit` ⇒ ffmpeg amix (စကားလုံးအချိန်တိတိ)
   ▼
core/beatqc.py  (base↔out frame diff bbox · Vision မျက်နှာ · caption ဇုန် · edge · blackout)
   │  ပြဿနာ ⇒ pos လှန် / ဖယ် ⇒ ပြင်ထားသော window သာ ပြန် render (cache)
   ▼
ထွက်ဖိုင် + Visual Plan (`beat.<type>` rows) ⇒ editor မှာ ကြည့် · လဲ · ဖြုတ် · စာ/ဂဏန်း ပြင်
```

## ဖိုင်များ

| ဖိုင် | တာဝန် |
|---|---|
| `core/beat_registry.json` | **တစ်ခုတည်းသော အမှန်** — type ၃၃ · params schema · dur · zone · SFX · example · `hit` |
| `~/ikki-remotion/src/kit/registry.json` | အထက်ပါ ကော်ပီ (test `test_registry_in_sync_with_remotion` က စစ်) |
| `~/ikki-remotion/src/kit/{base,ui,data,flow,Beats}.tsx` | Remotion component များ · brand context · auto-fit text · Lucide icon |
| `core/director.py` | AI director (Gemini + rules) · validate · schedule (density/spacing/variety/placement) |
| `core/brandkit.py` | user brand ⇒ accent/accent2/ink + style pack (glass/light/neon · radius) |
| `core/remo.py` | `compose_beats` · `sfx_events` · `_windows` |
| `core/beatqc.py` | auto-QC + vision critic (ရွေးချယ်) |
| `api/main.py` | `POST /api/jobs/{id}/beats` · `GET /api/beats/registry` |
| `web/script.html` | Visual Plan ထဲ beat rows · preview video · ပြင်မယ် form |
| `tools/beatprev.py` | `web/tplprev/beat.<type>.{mp4,jpg}` ပြန်ထုတ် |
| `ikki-audit/worker-run-beats.patch` | worker hook (`engine="beats"`) |

## Library (၃၃ မျိုး)

* **Realistic UI** — notify (iOS banner) · chat (typing → bubble) · vs (red/green glow) · user_tag (✓) · post
  (like counter) · search (typing) · comment · progress · app_icons · big_caption
* **Data** — stat (odometer) · ring · bars · line · donut · stat_grid · countdown (clock) · rating
* **Flow** — steps · checklist · list · timeline · before_after · qa
* **Emphasis** — brand · transfer · date · quote · profile · warning · location · icon_kw · cta

Variant ၃ မျိုး (glass · light · neon) × radius × brand accent ⇒ user တိုင်း ပုံစံ ကွဲ။
⚠️ တကယ့် logo/brand asset မသုံး — initials tile (KBZPay ⇒ KBZ)။

## Timing + SFX design system

* beat `at` = anchor စကားလုံး **စချိန်** (output timeline `o0`)။ entry က `PRE = 4f` စောပြီး spring ⇒ peak ≈ စကားလုံး။
* SFX `[role, frame_offset@30, vol]` — ffmpeg က `at + off/30 − hit[role]` မှာ စ ⇒ **transient က beat မှာ ကျ**။
  `hit` = ဖိုင်တိုင်းကို တိုင်းထားသော peak 50% အချိန် (`registry.hit`)။
* အသံ ၃၀ ခု (public/sfx): whoosh · swipe · pop · click · snap · type_tick · impact · riser · shimmer ·
  clock_tick/clock_fast/tick_counter (Mixkit free) · blade_swish/slide/whoosh (Mixkit free) ·
  tx_* (data_stream · glitch_burst/long · radio_scan · shimmer · sparkle · tape_stop · twinkle · vinyl_crackle — IKKI gen) ·
  p_* (message_in · whoosh_bright_air · glitch_soft · page_flip · sparkle_soft — IKKI premium)
* density pack — `calm` 4/min · `default` 6/min · `hype` 9/min · gap 2.6–5s · center cutaway gap 10–25s ·
  type တူ ဆက်တိုက် ⇒ variant ပြောင်း · ဂဏန်းတူ (500,000) ⇒ တစ်ခါသာ။

## Placement + QC

* zone: `side` (မျက်နှာ ဘယ်ဆို ညာ) · `top` · `bottom` (caption အပေါ်) · `center` (scrim ပါ cutaway — မျက်နှာ ဖုံးခွင့်)
* QC တိုင်းချက် (ထွက်ပြီးသား ပုံ): face cover > 12% ⇒ pos လှန် ⇒ ဒုတိယ မရ ⇒ ဖယ် · caption ဇုန် · edge · blackout
* ⚠️ box-shadow ကြောင့် diff bbox ပွ ⇒ core threshold 70 + margin 1.5% (WU v9 မှာ တွေ့ပြီး ပြင်)
* ⚠️ Remotion TMPDIR ကို exFAT (/Volumes/a) သို့ မပြောင်းရ — OffthreadVideo နောက်ခံ အမည်း ထွက် (တိုင်းပြီး)
* vision critic — `IKKI_VISION_CRITIC=1` ⇒ contact sheet ⇒ Gemini rubric (readability · premium · clutter · face)

## Recipe keys (headtop)

`engine="beats"` · `beat_pack` · `director_ai` · `beat_cta` · `beat_sfx_gain` · `brand_kit` (dict · ရွေးချယ်) ·
`beat_variant` · `beat_radius`။ patch မတပ်ခင် `engine="beats"` ကို worker က မသိ ⇒ IKKI ကတ် အတိုင်း (ဘေးကင်း)။

## Editor

Visual Plan ထဲ `✦` row = beat · preview video · 「ဒီအတိုင်း / ပြင်မယ် / ဖြုတ်」။ 「ပြင်မယ်」 ⇒ type လဲ · နေရာ ·
style · param (စာရင်း = တစ်ကြောင်း တစ်ခု · တွဲ = `a | b`)။ 「အလှအပ ပြန်ထုတ်」 ⇒ `/beats` ⇒ `/vplan` ⇒ `/revis`။
