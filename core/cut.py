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


def guard(drops, sp, tail=0.0, lead=0.0):
    """ဖျက်မည့် အပိုင်းများကို **လူ့ ဖြတ်မှတ် အလေ့အထ** အတိုင်း ချုံ့ပေးသည်。

    tail = ချန်မည့် စကား run အဆုံးပြီး ဤအချိန်အထိ ထပ်ချန် (အဆုံးသတ် အမြီး မပြတ်စေရန်)
    lead = နောက် စကား run အစ မတိုင်မီ ဤအချိန်မှ ပြန်စ (ဦးခေါင်း pre-roll)

    ⚠️ Zin ၏ YouTube အပြီးသတ်ကို တိုင်း၍ ရသော ကိန်းများ (calib `edit`)。
       tail ဦးစားပေး — ကွက်လပ် မဆံ့လျှင် lead ကို လျှော့သည်
       (「အဆုံးသတ် ပြတ်တာက ပိုဆိုး」 — Zin ၂၀၂၆-၀၉-၁၈)。
    ⚠️ စကား run **ထဲ ဘယ်တော့မှ မဝင်ရ** — ဖျက်ရမည့် စကား ပြန်ပေါ်လာမည်。
    """
    if not drops or (tail <= 0 and lead <= 0): return [list(x) for x in drops]
    out = []
    for a, b in drops:
        a, b = float(a), float(b)
        pe = max((y for x, y in sp if y <= a + 1e-9), default=None)
        do = min((x for x, y in sp if x >= (pe if pe is not None else a)), default=None)
        de = max((y for x, y in sp if y <= b + 1e-9), default=None)
        ko = min((x for x, y in sp if x >= b - 1e-9), default=None)
        a2 = a if pe is None else min(pe + tail, (do - 0.02) if do is not None else b)
        b2 = b if ko is None else max((de + 0.02) if de is not None else a, ko - lead)
        if b2 <= a2 + 0.05:                       # ကွက်လပ် မဆံ့ ⇒ tail ဦးစားပေး
            b2 = min(b, a2 + 0.05)
            if b2 <= a2: a2, b2 = a, b
        if b2 - a2 > 0.05: out.append([max(a2, 0.0), b2])
    return out


def quiet_at(t, db, hop, win=0.35):
    """`t` ရဲ့ ±win အတွင်း **စွမ်းအင် အနိမ့်ဆုံး** အချိန် — မရလျှင် `t`。

    ⚠️ ဤစပီကာလို **ဆက်တိုက် ပြောသူ**များမှာ တကယ့် တိတ်ဆိတ်မှု မရှိသလောက်
       ဖြစ်သည် (၇၇.၇s မှာ ၃.၆s ပဲ)。 ဝါကျ နယ်နိမိတ် ၂၂ ခုထဲ ၁၈ ခု (၈၁%) က
       စကား run ရဲ့ **အလယ်** မှာ ကျပြီး တချို့က အနားကနေ ၂–၆s ဝေးသည်
       (၂၀၂၆-၀၉-၂၀ တိုင်းထားသည်)。 ⇒ တိတ်ဆိတ်မှုကိုပဲ ရှာနေလျှင် ဘယ်တော့မှ
       မတွေ့ဘဲ ASR ရဲ့ ကြမ်းသော အချိန်မှတ်အတိုင်း ဖြတ်မိပြီး —
         · ဖျက်လိုက်သော ဝါကျရဲ့ အသံ **ကျန်နေ**သည်
         · ဖြတ်ဆက်က **ကြမ်း**သည် (Zin: 「အဆုံးသတ်လေးတွေသိပ်မလှဘူး」)
       တိုင်းချက် — အနိမ့်ဆုံးမှတ်ဆီ ရွှေ့လျှင် ဖြတ်မှတ်ရဲ့ စွမ်းအင်
       **အလယ်တန်း ၂၄.၃ dB ကျ**သည် (p25 ၁၆.၃ · p75 ၂၈.၇) · ရွှေ့ရတာ ၀.၂၀s。
    """
    if db is None or not hop: return t
    n = len(db)
    i = int(round(t / hop))
    if i <= 0 or i >= n: return t
    lo = max(0, int((t - win) / hop)); hi = min(n, int((t + win) / hop) + 1)
    if hi - lo < 2: return t
    j = lo + min(range(hi - lo), key=lambda k: db[lo + k])
    return j * hop


def subtract(spans, drop, sil=None, snap=0.35, min_keep=MIN_KEEP_RUN,
             db=None, hop=None):
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
        # ① တကယ့် တိတ်ဆိတ်မှု အနားသတ် ရှိလျှင် အဲဒါ အကောင်းဆုံး
        if edges:
            c = min(edges, key=lambda e: abs(e - t))
            if abs(c - t) <= snap and lo <= c <= hi: return c
        # ② မရှိလျှင် **စွမ်းအင် အနိမ့်ဆုံးမှတ်** — ASR ရဲ့ ကြမ်းသော
        #    အချိန်မှတ်အတိုင်း ဖြတ်တာထက် အလယ်တန်း ၂၄ dB တိတ်သည်。
        q = quiet_at(t, db, hop, snap)
        return q if lo <= q <= hi else t
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


# ══ `_drop_exact` ကာကွယ်ချက် (Cut audit P0) ═══════════════════════
# ⚠️ သုံးစွဲသူ လက်ခံထားသော ပြန်စ အပိုင်းများကို အရင်က **စစ်ဆေးမှု မရှိဘဲ**
#    `subtract(..., snap=0.0)` ကို တိုက်ရိုက် ပို့ခဲ့သည်。 ဒါက —
#      · စကားထဲ ကျနေသော အစွန်းကို ဖြတ်ပြီး **စကားလုံး ဖြတ်**နိုင်သည်
#        (Zin ရဲ့ ပထမ စည်းကမ်း: စကားထဲ ဘယ်တော့မှ မဖြတ်ရ · F2 = 0)
#      · အပိုင်းချင်း ထပ်နေလျှင် ဖြုတ်ချက် နှစ်ဆ တွက်မိသည်
#      · ဗီဒီယို တစ်ခုလုံး ပျောက်သွားအောင် ဖြတ်မိနိုင်သည်
#    ⇒ **ပိတ်ပြီး အကြောင်းရင်း ပြရမည်** — တိတ်တဆိတ် ဖြတ်တာ မဟုတ်。
EDGE_PAD = 0.04          # စကား အစွန်းနဲ့ ဤအကွာအဝေးထက် နီးလျှင် မလုံခြုံ
MIN_DROP = 0.08          # ဒီထက် တိုသော ဖျက်ချက်က အဓိပ္ပာယ် မရှိ
MIN_LEFT = 1.0           # ဗီဒီယိုမှာ အနည်းဆုံး ကျန်ရမည့် စက္ကန့်


def validate_drops(drops, sp, dur, edge=EDGE_PAD, min_drop=MIN_DROP,
                   min_left=MIN_LEFT, kept=None):
    """`(ok, bad)` — `ok` က ဖြတ်လို့ရသော အပိုင်း · `bad` က `(အပိုင်း, အကြောင်းရင်း)`

    `sp`   — စကား run စာရင်း `[(a, b)]` (`measure.speech()[0]`)
    `dur`  — မူရင်း ကြာချိန်
    `kept` — ယခု ကျန်နေသော span စုစုပေါင်း စက္ကန့် (ရှိလျှင် အနည်းဆုံး စစ်သည်)

    ⚠️ **အစွန်း ၂ ဖက်လုံး** စကားထဲ မကျရ — တစ်ဖက်ဖက် ကျလျှင် စကားလုံး
       ပြတ်သည်。 `measure.in_speech()` က pad နဲ့ စစ်သည်。
    """
    try:
        import measure as _M
    except ImportError:
        from core import measure as _M
    ok, bad, taken = [], [], []
    for d in (drops or []):
        try:
            a, b = float(d[0]), float(d[1])
        except (TypeError, ValueError, IndexError):
            bad.append((d, "ကိန်း မဟုတ်")); continue
        if not (a == a and b == b) or a in (float("inf"), float("-inf")) \
                or b in (float("inf"), float("-inf")):
            bad.append((d, "ကိန်း မမှန်")); continue
        if b <= a:
            bad.append((d, "အဆုံးက အစထက် မကြီး")); continue
        if a < -1e-6 or (dur and b > float(dur) + 0.05):
            bad.append((d, f"မူရင်း ကြာချိန် ({dur:.1f}s) ပြင်ပ")); continue
        if b - a < min_drop:
            bad.append((d, f"တိုလွန်း ({b-a:.2f}s < {min_drop}s)")); continue
        if any(a < y - 1e-9 and b > x + 1e-9 for x, y in taken):
            bad.append((d, "အရင် ဖျက်ချက်နဲ့ ထပ်နေသည်")); continue
        # ⚠️ အစွန်း ၂ ဖက်လုံး စကားထဲ မကျရ
        ina = _M.in_speech(a, sp, pad=edge) if sp else False
        inb = _M.in_speech(b, sp, pad=edge) if sp else False
        if ina or inb:
            side = "အစ" if ina and not inb else ("အဆုံး" if inb and not ina
                                                 else "အစ+အဆုံး")
            bad.append((d, f"{side} က စကားထဲ ကျနေသည် — စကားလုံး ပြတ်မည်"))
            continue
        ok.append([a, b]); taken.append((a, b))
    if kept is not None:
        rm = sum(y - x for x, y in taken)
        if kept - rm < min_left:
            # ⚠️ အားလုံး ဖျက်မိလျှင် ဗီဒီယို မကျန်တော့ ⇒ တစ်ခုမှ မဖျက်ရ
            return [], [(d, f"အားလုံး ဖျက်လျှင် {kept-rm:.1f}s သာ ကျန်မည် "
                            f"(အနည်းဆုံး {min_left}s)") for d in (drops or [])]
    return ok, bad


def readd(spans, keep, dur):
    """ဖြတ်ထားသော အပိုင်းများကို **ပြန်ပေါင်း**သည် — `(spans, ပြန်ထည့် s)`

    ⚠️ engine က တိတ်ဆိတ်မှုကို ပုံသေ ဖြတ်သည် — ဒါပေမယ့် အနားယူချက် တချို့က
       တမင် ထားတာ ဖြစ်သည် (အသားပေးချက် · အသက်ရှူ · ရပ်တန့်ချက်)。
       Zin ၂၀၂၆-၀၉-၂၁: 「ဒီနေရာတွေပါ စိတ်ကြိုက် edit လို့ရအောင်」。
    ⚠️ **ဘောင်ပြင် မထွက်ရ** — `[0, dur]` အတွင်း clamp ပြီး ထပ်နေတာကို ပေါင်းသည်。
    ⚠️ ပြန်ပေါင်းပြီးနောက် span များက **အစီအစဉ်လိုက် · ထပ်မနေ** ဖြစ်ရမည် —
       မဟုတ်လျှင် `spans.spans()` က အပိုင်းအစ ထပ်ထုတ်ပြီး ဗီဒီယို ရှည်သွားမည်。
    """
    try:
        dur = float(dur)
    except (TypeError, ValueError):
        return spans, 0.0
    add = []
    for w in (keep or []):
        try:
            a, b = float(w[0]), float(w[1])
        except (TypeError, ValueError, IndexError):
            continue
        a = max(0.0, min(a, dur)); b = max(0.0, min(b, dur))
        if b - a > 0.02:
            add.append((a, b))
    if not add:
        return spans, 0.0
    before = sum(b - a for a, b in spans)
    out = []
    for a, b in sorted(list(spans) + add):
        if out and a <= out[-1][1] + 1e-6:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out, max(0.0, sum(b - a for a, b in out) - before)
