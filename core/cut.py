#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · ဖြတ်တောက် အစီအစဉ် ဆွဲခြင်း。

⚠️ စည်းမျဉ်း ၃ ခု (တိုင်းပြီး၍ သိရသည်) —
  ① ဖြတ်မှတ်က တိတ်ဆိတ်မှု **အထဲ**မှာသာ ရှိရမည်
  ② snap ပြီးမှ အနားယူချိန် ထပ်ထည့်လျှင် snap ပျက်သည် — အနားယူချိန်ကို
     တိတ်ဆိတ်မှု **အထဲကနေပဲ** ယူရမည် (ထည့်လျှင် ၂၈% ပြန်ဆိုးခဲ့သည်)
  ③ ဖြတ်လွန်းလျှင် အသက်ရှုသံ ပျောက်ပြီး စက်ဆန်သွားသည် — recipe က
     ဘယ်လောက် ချန်မလဲ ဆုံးဖြတ်ရသည် (Course က လုံးဝ မဖြတ်)
"""
import os
import measure as M

# ══ calibration ═════════════════════════════════════════════
# ⚠️ `cut_threshold` နဲ့ `pad` ဟာ **ချန်နယ်တစ်ခုချင်းစီ** ဖြစ်သည် —
#    တည်းဖြတ်သူရဲ့ အရသာကို ကိုယ်စားပြုသည်、စကားရဲ့ ပုံသဏ္ဍာန် မဟုတ်。
#    ZJL ရဲ့ ၀.၆၀/၀.၁၂ ကို ZAE ပေါ် သုံးလျှင် grade မှာ လုပ်မိသလို အမှား
#    ဖြစ်မည် ⇒ calib မရှိသော ချန်နယ်မှာ recipe ရဲ့ ကိန်းကို သုံးပြီး
#    အစီရင်ခံစာမှာ **"uncalibrated"** ဟု ပြရမည် (SKILL ရဲ့ F5)。
import json as _json
_CALDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "assets", "calib")
_CALMAP = {"zjl": "zin_japan_life"}
_CALC = {}

def calib(brand):
    """(dict|None) — ချန်နယ်အတွက် ချိန်ညှိချက်; မရှိလျှင် None。"""
    k = _CALMAP.get(brand or "", brand or "")
    if k in _CALC: return _CALC[k]
    try:
        _CALC[k] = _json.load(open(os.path.join(_CALDIR, k + ".json"), encoding="utf-8"))
    except Exception:
        _CALC[k] = None
    return _CALC[k]


MIN_KEEP_RUN = 0.25      # SKILL — ဒီထက် တိုသော အပိုင်းက စကားလုံး တုန်စေသည်
# ⚠️ ၀.၃၅ → ၀.၈၀ (Zin ၂၀၂၆-၀၉-၁၇) — ၀.၃၅ က နမူနာ ၁ ခု (happiness-3) ကနေ လာပြီး
#    ground truth ၆ ခုမှာ **လူကိုယ်တိုင် ၅၅.၃–၇၂.၈% ဖယ်**သည် ⇒ ၆ ခုလုံး ၀.၃၅ ကျော်。
#    zjl calib မှာ ၀.၈၀ ပြင်ပြီးသား ဖြစ်ပြီး calib မရှိသော brand (zae · AA Japan)
#    မှာသာ ၀.၃၅ ကျန်နေခဲ့သည်。 F1 က ယခု **သတိပေးချက်သာ** — job မပျက်。
MAX_REMOVED  = 0.80      # SKILL F1 — ဒီထက် ဖြတ်လျှင် သတိပေး


def plan(audio, keep_pause=0.34, min_sil=0.50, edge=0.06, brand=None, meas=None):
    """(spans, cuts, stats) — SKILL `ikki-cut-engine` အတိုင်း。

    spans = ထားမည့် (start, end) စာရင်း — trim+concat ဖြင့် ထုတ်ရန်
    keep_pause = တိတ်ဆိတ်မှုတိုင်းမှာ ချန်ထားမည့် အချိန် (= ၂×pad)
    min_sil    = ဒီထက် တိုသော တိတ်ဆိတ်မှုကို လုံးဝ မထိ (= cut_threshold)
    """
    # ⚠️ `meas` ပေးလာလျှင် **ထပ်မတွက်ရ** — ASR · cut · dress သုံးခုလုံး
    #    တိတ်ဆိတ်မှု မြေပုံ **တစ်ခုတည်း** သုံးရမည် (မတူလျှင် transcript
    #    နယ်နိမိတ်နှင့် ဖြတ်မှတ် ကွဲသွားသည်)。 စံ = ဤ `speech()` ဖြစ်သည် —
    #    ကိန်းသေများ calib လုပ်ပြီးသား。
    sp, sil, dur, ev, cls = meas if meas is not None else M.speech(audio)
    if not sp and not sil:
        return [], [], {"note": "အသံ မတွေ့", "refusals": ["F4"]}
    # ── F4: A-roll မရှိလျှင် ဖြတ်စရာ မရှိ ──
    if cls != "aroll":
        return [(0.0, dur)], [], dict(cls=cls, ev=ev, src_dur=round(dur,2),
            cuts=0, removed=0.0, in_speech=0, points=0, silences=len(sil),
            thr=ev.get("thr_db"), refusals=["F4"],
            note="B-roll — ဖြတ်စရာ စကား မရှိ")
    # ⚠️ **မှတ်တမ်းသာ** — ဦးစားပေး အစီအစဉ်ကို ဒီမှာ မပြောင်းပါ (အဆင့် ၁.၂)。
    #    ဘယ်ကိန်း တကယ် အသုံးဝင်လဲ report မှာ ပြနိုင်ရန် `src` သိမ်းသည်。
    src = "recipe/default"
    cal = calib(brand)
    if cal:
        if "cut_threshold_s" in cal or "pad_s" in cal: src = "calib"
        min_sil    = float(cal.get("cut_threshold_s", min_sil))
        keep_pause = 2.0*float(cal.get("pad_s", keep_pause/2.0))
    pad = keep_pause/2.0
    # ⚠️ F1 ကန့်သတ်ချက်ကို **calib ကနေ** ယူသည် (R5) — မရှိလျှင် module default
    max_removed = float((cal or {}).get("max_removed_ratio", MAX_REMOVED))

    spans=[]; cuts=[]; pos=0.0
    for a, b in sil:
        if b-a <= min_sil: continue                 # တိုသော အနားယူချိန် — မထိ
        ca = a + pad; cb = b - pad                  # ⚠️ တိတ်ဆိတ်မှု **အထဲက** ယူ
        if cb - ca < 0.08: continue
        if ca - pos >= MIN_KEEP_RUN: spans.append((pos, ca))
        elif spans:                                 # F3 — တိုလွန်းလျှင် ပေါင်း
            spans[-1] = (spans[-1][0], ca)
        cuts.append(dict(at=round(ca,3), to=round(cb,3),
                         removed=round(cb-ca,3), kind="silence"))
        pos = cb
    if dur - pos >= MIN_KEEP_RUN: spans.append((pos, dur))
    elif spans: spans[-1] = (spans[-1][0], dur)

    removed = sum(c["removed"] for c in cuts)
    pts = [c["at"] for c in cuts] + [c["to"] for c in cuts]
    bad = [t for t in pts if M.in_speech(t, sp)]
    ratio = (removed/dur) if dur else 0.0
    short = [round(b-a,2) for a,b in spans if b-a < MIN_KEEP_RUN]
    refus=[]; warn=[]
    # ⚠️ F1 က **သတိပေးချက်သာ** (Zin ၂၀၂၆-၀၉-၁၆) — ဖယ်တာ များတိုင်း ဗီဒီယို
    #    မထုတ်ဘဲ job ပျက်စေခဲ့သည်။ ground truth ၆ ခုမှာ လူကိုယ်တိုင် ၅၅.၃–၇၂.၈%
    #    ဖယ်သည် ⇒ "များသည်" ဆိုတာ အမှား မဟုတ်။ runaway bug ဖမ်းရန်သာ ကျန်။
    if ratio > max_removed:
        warn.append(f"F1 removed_ratio {ratio:.3f} > {max_removed} — ဖယ်တာ များ (ထုတ်သည် · စစ်ကြည့်ပါ)")
    if bad:   refus.append(f"F2 ဖြတ်မှတ် {len(bad)} ခု စကားပေါ် ကျသည်")
    if short: refus.append(f"F3 တိုလွန်းသော အပိုင်း {short}")
    st = dict(cuts=len(cuts), points=len(pts), in_speech=len(bad),
              removed=round(removed,2), removed_ratio=round(ratio,3),
              src_dur=round(dur,2), silences=len(sil), thr=ev.get("thr_db"),
              cls=cls, ev=ev, calibrated=bool(cal),
              calib_src=(cal or {}).get("calibrated_against"),
              cut_threshold=round(min_sil,3), pad=round(pad,3),
              max_removed=max_removed,
              cut_src=src, refusals=refus, warnings=warn)
    return spans, cuts, st


def subtract(spans, drop, sil=None, snap=0.35, min_keep=MIN_KEEP_RUN):
    """သုံးစွဲသူ ဖျက်ထားသော အချိန်အပိုင်းများကို `spans` ကနေ **တကယ် နုတ်**သည်。

    ⚠️ transcript ကနေ စာကြောင်း ဖျက်လိုက်တာက အရင်က **စာတန်းကိုပဲ** ဖယ်ခဲ့ပြီး
       ရုပ်နဲ့ အသံက ကျန်နေခဲ့သည် (`CUT.plan` က တိတ်ဆိတ်မှုပဲ ဖြတ်၍)。
       Zin: "ဖြတ်ထားတာကို သဘောမကျရင်ရော" ⇒ ဖျက်လျှင် **တကယ် ဖြတ်ရမည်**。
    ⚠️ ဖြတ်မှတ်ကို ဖြစ်နိုင်လျှင် **တိတ်ဆိတ်မှုထဲ ဆွဲသွင်း**သည် (±snap) —
       စကားလုံးအလယ် ဖြတ်လျှင် နားထောင်ရ ဆိုးသည် (R3)。 အနီးမှာ တိတ်ဆိတ်မှု
       မရှိလျှင်တော့ သုံးစွဲသူ ရွေးထားတဲ့ နယ်နိမိတ်အတိုင်း ဖြတ်သည် —
       အကြောင်းအရာ ဖြတ်ချက်က တိတ်ဆိတ်မှု ဖြတ်ချက် မဟုတ်。
    """
    if not drop: return spans, 0.0
    edges = []
    for a, b in (sil or []):
        edges.append(a); edges.append(b)
    def snapto(t, lo, hi):
        if not edges: return t
        c = min(edges, key=lambda e: abs(e - t))
        return c if (abs(c - t) <= snap and lo <= c <= hi) else t
    cuts = []
    for a, b in sorted(drop):
        a2 = snapto(float(a), float(a) - snap, float(b))
        b2 = snapto(float(b), float(a), float(b) + snap)
        if b2 - a2 > 0.05: cuts.append((a2, b2))
    out = []
    for s0, s1 in spans:
        cur = [(s0, s1)]
        for a, b in cuts:
            nxt = []
            for x, y in cur:
                if b <= x or a >= y: nxt.append((x, y)); continue
                if x < a: nxt.append((x, a))
                if b < y: nxt.append((b, y))
            cur = nxt
        out.extend(cur)
    out = [(a, b) for a, b in out if b - a >= min_keep]
    removed = sum(b - a for a, b in spans) - sum(b - a for a, b in out)
    return out, round(removed, 2)
