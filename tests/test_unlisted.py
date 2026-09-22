# -*- coding: utf-8 -*-
"""**ချန်ထားပြီး ဝါကျ မရှိသော ပိုင်းများ** — `cut.unlisted()`。

⚠️ Zin ၂၀၂၆-၀၉-၂၂: 「Script editor မှာ ဖြတ်ခဲ့ပေမယ့် ဗီဒီယိုထဲ ပါနေတယ် ·
   မင်းပြတာ မပြည့်စုံဘူး」。 တိုင်းချက် (j_58639d6961da): ဖျက်ခိုင်းထားသော
   ဝါကျ ၆ ခုလုံး ဖြုတ်ပြီး (ကျန် ၀.၀၀s) — ဒါပေမယ့် ထွက်ချက် ၆၉.၅s ရဲ့
   **၁၂.၆s (၁၈%)** က Script Editor မှာ **တစ်ခါမှ မပေါ်ခဲ့သော ပိုင်းများ**
   (out 0:00 · 0:30–0:32 · 0:40–0:45 · 1:03–1:07 — Zin ပြောသည့် နေရာအတိအကျ)。
⚠️ စည်းကမ်း: engine က ဒီပိုင်းတွေကို **မဖြတ်ရ** — စာရင်းသာ ထုတ်ပြီး
   သုံးစွဲသူ နားထောင်ပြီးမှ ဖြတ်ရမည် (「ဖြတ်ရတာ ခက်ရင် မဖြတ်နဲ့」)。
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), "core"))
import cut as CUT

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")

def segs(*iv): return [dict(start=a, end=b, text="x") for a, b in iv]

print("── ① ဝါကျနဲ့ အတိအကျ ကိုက်လျှင် ဘာမှ မရှိ ──")
r = CUT.unlisted([(10.0, 20.0)], segs((10.0, 20.0)), 30.0)
ck("ဗလာ", r == [], r)

print("\n── ② ချန်ထားပြီး ဝါကျ မရှိသော ပိုင်း ⇒ တွေ့ရမည် ──")
r = CUT.unlisted([(10.0, 20.0)], segs((10.0, 13.0), (17.0, 20.0)), 30.0)
ck("၁ ကြောင်း", len(r) == 1, r)
ck("နယ်နိမိတ် မှန် (pad ပါ)",
   abs(r[0]["a"] - 13.3) < 0.01 and abs(r[0]["b"] - 16.7) < 0.01, r)

print("\n── ③ ဖြတ်ပစ်လိုက်သော ပိုင်းကို **မပြရ** ──")
# 20–40 ကို ဖြတ်ပစ်ပြီး (span မဟုတ်) ⇒ ထွက်ချက်ထဲ မပါ ⇒ row မလို
r = CUT.unlisted([(0.0, 20.0), (40.0, 50.0)], segs((0.0, 20.0), (40.0, 50.0)), 60.0)
ck("ဗလာ (ဖြတ်ပစ်ပြီးသား)", r == [], r)

print("\n── ④ တိုလွန်းလျှင် မပြ ──")
r = CUT.unlisted([(10.0, 20.0)], segs((10.0, 14.9), (15.1, 20.0)), 30.0)
ck("၀.၂s အောက် ⇒ ဗလာ", r == [], r)

print("\n── ⑤ နီးစပ်သော အပိုင်းအစများ **ပေါင်း** ──")
# ⚠️ ကြားက ဝါကျ တိုသဖြင့် အပိုင်းအစ ၂ ခု ဖြစ်ပြီး အချင်းချင်း ၀.၆s
#    ကွာသည် ⇒ `merge_gap` ၀.၈ အောက် ⇒ **ပေါင်းရမည်**。
r = CUT.unlisted([(0.0, 20.0)], segs((0.0, 5.0), (6.0, 6.4), (7.0, 13.0)),
                 30.0, pad=0.1)
_near = [x for x in r if x["a"] < 7.0]
ck("နီးစပ်သော ၂ ခု ⇒ ၁ ကြောင်း", len(_near) == 1, r)
ck("ပေါင်းပြီး နယ်နိမိတ် ကျယ်", _near and _near[0]["dur"] >= 1.5, _near)
# ⚠️ ကွာလွန်းလျှင် **မပေါင်းရ** — တစ်နေရာတည်း ဟု မှားပြလျှင် နားထောင်ရ ခက်မည်
r2 = CUT.unlisted([(0.0, 30.0)], segs((0.0, 5.0), (6.5, 7.0), (8.0, 13.0)), 40.0)
ck("၁.၁s ကွာ ⇒ မပေါင်း (ခွဲပြ)", len(r2) == 3, r2)

print("\n── ⑥ စကား ပါမပါ ခွဲ (meas ပါလျှင်) ──")
# meas[0] = စကား run များ
meas = ([(13.5, 16.5)], [], 30.0, {}, "aroll")
r = CUT.unlisted([(10.0, 20.0)], segs((10.0, 13.0), (17.0, 20.0)), 30.0, meas=meas)
ck("kind = speech", r and r[0]["kind"] == "speech", r)
ck("စကား စက္ကန့် တိုင်းထား", r and (r[0]["speech"] or 0) > 2.0, r)
meas2 = ([(0.0, 1.0)], [], 30.0, {}, "aroll")
r2 = CUT.unlisted([(10.0, 20.0)], segs((10.0, 13.0), (17.0, 20.0)), 30.0, meas=meas2)
ck("စကား မပါ ⇒ quiet", r2 and r2[0]["kind"] == "quiet", r2)
r3 = CUT.unlisted([(10.0, 20.0)], segs((10.0, 13.0), (17.0, 20.0)), 30.0)
ck("meas မပါ ⇒ unknown (မှန်းမပြ)", r3 and r3[0]["kind"] == "unknown", r3)

print("\n── ⑦ ကျဘမ်း မဖြစ်ရ ──")
for bad in ([], None):
    ck(f"spans={bad} ⇒ ဗလာ", CUT.unlisted(bad, segs((0.0, 5.0)), 10.0) == [])
ck("segs မရှိ ⇒ span တစ်ခုလုံး ပြ",
   len(CUT.unlisted([(0.0, 10.0)], [], 10.0)) == 1)
ck("segs=None ⇒ ကျဘမ်း မဖြစ်",
   len(CUT.unlisted([(0.0, 10.0)], None, 10.0)) == 1)
ck("မမှန်သော segs ကို ကျော်",
   len(CUT.unlisted([(0.0, 10.0)], [{"start": None, "end": "x"}], 10.0)) == 1)

print("\n── ⑧ Zin ရဲ့ တကယ့် job (j_58639d6961da) ──")
# ⚠️ တကယ့် ဖြတ်မှတ် ၃၂ ခုကနေ ယူထားသော အပိုင်း — out 0:40–0:45 ဖြစ်သော နေရာ
REAL_SPANS = [(134.08, 136.38), (137.36, 139.26), (139.86, 140.20),
              (140.74, 141.34), (143.22, 143.54), (145.0, 152.8)]
REAL_SEGS = segs((145.26, 152.46))
r = CUT.unlisted(REAL_SPANS, REAL_SEGS, 178.68)
ck("ဝါကျ မရှိသော ပိုင်း တွေ့", len(r) >= 1, r)
_tot = sum(x["dur"] for x in r)
ck("စုစုပေါင်း ≥ 6s (မမြင်ရခဲ့သော အသံ)", _tot >= 6.0, round(_tot, 2))
ck("ဝါကျ ရှိသော ပိုင်း (145.26–152.46) မပါ",
   not [x for x in r if x["a"] >= 145.5 and x["b"] <= 152.2], r)

print("\n── ⑨ engine က **မဖြတ်ပါ** (စာရင်းသာ) ──")
sp0 = [(10.0, 20.0)]
CUT.unlisted(sp0, segs((10.0, 13.0)), 30.0)
ck("spans မထိ", sp0 == [(10.0, 20.0)], sp0)
sg0 = segs((10.0, 13.0))
CUT.unlisted([(10.0, 20.0)], sg0, 30.0)
ck("segs မထိ", sg0 == segs((10.0, 13.0)))



# ══════════════════════════════════════════════════════════════════════
# ⑩ **အာမခံချက်** — ဗီဒီယို ပုံစံ ကျပန်း ၂၀၀၀ ခု
# ══════════════════════════════════════════════════════════════════════
# ⚠️ Zin ၂၀၂၆-၀၉-၂၂: 「အခြား video တွေတင်လိုက်လဲ အသံတွေအားလုံးကို
#    သေချာ ဖမ်းနိုင်ပြီလား」 ⇒ **မှန်းလို့ မရ**。 ကျပန်း အခင်းအကျင်းတွေနဲ့
#    ပြပြရမည်: ချန်ထားပြီး ဝါကျ မရှိသော အချိန် တစ်စက္ကန့်တိုင်း
#    (run ≥ `min_d`) က ပြန်လာသော စာရင်းထဲ **မဖြစ်မနေ ပါရမည်**。
import random

print("\n── ⑩ ကျပန်း ဗီဒီယို ပုံစံ ၂၀၀၀ ခု — အားလုံး ဖမ်းမိလား ──")
random.seed(20260922)
STEP = 0.05
bad_cases = 0
worst = None
total_missed = 0.0
checked = 0
for case in range(2000):
    dur = random.uniform(20.0, 600.0)
    # ── ဝါကျများ (ကျပန်း အရှည် · ကျပန်း ကွာဟမှု) ──
    sg = []
    t = random.uniform(0.0, min(30.0, dur * 0.2))
    while t < dur - 1.0:
        ln = random.uniform(0.4, 9.0)
        if t + ln > dur: break
        sg.append((round(t, 2), round(t + ln, 2)))
        t += ln + random.choice([0.05, 0.2, 0.5, 1.0, 3.0, 8.0, 20.0]) * random.random()
    # ── ချန်မည့် span များ (ဝါကျနဲ့ မတူ · ကျပန်း) ──
    spans = []
    t = 0.0
    while t < dur:
        ln = random.uniform(0.5, 25.0)
        b = min(dur, t + ln)
        if b - t > 0.2: spans.append((round(t, 2), round(b, 2)))
        t = b + random.uniform(0.0, 12.0)
    if not spans: continue
    segs_ = [dict(start=a, end=b, text="x") for a, b in sg]
    res = CUT.unlisted(spans, segs_, dur)
    # ── သီးသန့် စစ်ချက် (function ကို မယုံဘဲ ကိုယ်တိုင် တွက်) ──
    pad = CUT.UNL_PAD
    sent = [(a - pad, b + pad) for a, b in sg]
    covered = [(x["a"], x["b"]) for x in res]
    # ချန်ထားပြီး ဝါကျ မရှိသော အချိန် run များ
    runs = []
    cur = None
    for a, b in spans:
        t = a
        while t < b:
            insent = any(p <= t <= q for p, q in sent)
            if not insent:
                if cur and abs(t - cur[1]) < STEP * 1.5: cur[1] = t + STEP
                else:
                    if cur: runs.append(cur)
                    cur = [t, t + STEP]
            t += STEP
    if cur: runs.append(cur)
    # run ≥ min_d ဖြစ်လျှင် စာရင်းထဲ ပါရမည်
    for r0, r1 in runs:
        if r1 - r0 < CUT.UNL_MIN + STEP: continue    # ကန့်သတ်နဲ့ နီးလျှင် ချွင်း
        mid = (r0 + r1) / 2.0
        checked += 1
        if not any(a - 0.1 <= mid <= b + 0.1 for a, b in covered):
            bad_cases += 1
            total_missed += r1 - r0
            if worst is None or (r1 - r0) > worst[1] - worst[0]:
                worst = (r0, r1)
print(f"  စစ်ခဲ့သော run {checked} ခု · **ကျော်သွားတာ {bad_cases} ခု**")
ck("ချန်ထားပြီး ဝါကျ မရှိသော run တိုင်း ဖမ်းမိ", bad_cases == 0,
   f"{bad_cases} ခု · {total_missed:.1f}s · အကြီးဆုံး {worst}")
ck("စစ်ချက် အလုံအလောက် ပြေးခဲ့", checked > 3000, checked)

print("\n── ⑪ ကန့်သတ်ချက်များ — **ရှင်းရှင်း မှတ်ထားရန်** ──")
# ⚠️ ဤ ၂ ချက်က **တမင် ထားသော** ကန့်သတ်ချက်များ — မဖမ်းမိတာ ရှိသည်。
r = CUT.unlisted([(0.0, 10.0)], segs((0.0, 5.0), (5.2, 10.0)), 10.0)
ck(f"ဝါကျ ၂ ခုကြား ၀.၂s ⇒ မပြ (min_d={CUT.UNL_MIN}s)", r == [], r)
r = CUT.unlisted([(0.0, 10.0)], segs((0.0, 5.0), (5.5, 10.0)), 10.0, pad=0.3)
ck(f"pad {CUT.UNL_PAD}s အတွင်း ⇒ ဝါကျရဲ့ အပိုင်း ဟု ယူ", r == [], r)
r = CUT.unlisted([(0.0, 10.0)], segs((0.0, 5.0), (6.0, 10.0)), 10.0)
ck("၁.၀s ⇒ ပြ", len(r) == 1 and r[0]["dur"] >= 0.35, r)

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
