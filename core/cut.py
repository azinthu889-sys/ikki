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


# ══ အနားယူချိန် ပြန်ပေးခြင်း ═══════════════════════════════════════
# ⚠️⚠️ ယခင်က တိတ်ဆိတ်မှု **အရှည် ဘယ်လောက်ပဲဖြစ်ဖြစ်** `2×pad` ပဲ ချန်ခဲ့သည်
#    ⇒ ၁၄.၉s အနားယူချိန်နဲ့ ၀.၅s အနားယူချိန် **ရလဒ် တူတူ**。 တိုင်းချက်
#    (၂၀၂၆-၁၀-၀၂ · short-916 ထွက်ဖိုင်): အနားယူချိန် **အရှည်ဆုံး ၀.၈၈s** ·
#    p90 ၀.၄၂s ⇒ စည်းချက် ပြားသွားသည်。
# ⚠️ Zin ရဲ့ **ကိုယ်ပိုင် ဗီဒီယို ၁၀ ခု** (ZJL knowledge) ကနေ တိုင်းချက် —
#      p50 ၀.၁၆ · p75 ၀.၃၆ · **p90 ၀.၅၆** · အရှည်ဆုံး ၁.၄–၁၃.၀ (အလယ် ၄.၉)
#    တိုတဲ့အနားတွေက ကိုက်နေပြီး **အရှည်ပဲ ကွာ**သည်。
# ⇒ မူရင်း အရှည်အလိုက် **အချိုးကျ ချန်**သည် (ပြောသူ ကိုယ်တိုင် ရပ်ထားတာက
#   ခေါင်းစဉ် ပြောင်းချက် ဖြစ်သည် — cut အဆင့်မှာ label မရသေး၍ ဒါက
#   တစ်ခုတည်းသော အချက်ပြ)。
# ⚠️ ကိန်းကို **ညှိပြီး ရွေးထားသည်** (မှန်းချက် မဟုတ်) — ratio ၀.၁၀ ·
#    အများဆုံး ၁.၅s ⇒ p90 **၀.၅၈** (ပစ်မှတ် ၀.၅၆) · ဗီဒီယို +၉.၆%。
# ⚠️⚠️ **`pause_keep()` (pause_ratio/pause_max) ကို ဖယ်လိုက်သည်**
#    (၂၀၂၆-၁၀-၀၃ · Zin: Descript ရဲ့ 「Shorten word gaps」 ကို ကြည့်ပြီး
#    「ကိန်း ၂ လုံးနဲ့ အစားထိုးပြီး လုပ်ပေးပါ」)。
#    အဲဒါက `(keep_pause, min_sil)` အပေါ် **ဒုတိယ ယန္တရား** ဖြစ်ပြီး —
#    ကွက်လပ် ရှည်လေ ပိုချန်လေ (၁.၅s အထိ)。 ချို့ယွင်းချက် ၂ ခု:
#      · **ကိန်းက ပြောတာနဲ့ တကယ် ဖြစ်တာ မတူ** — 「၀.၇၅s ထက် ရှည်ရင်
#        ၀.၄၀s ဖြစ်အောင်」 ဟု ဆိုပေမယ့် ရှည်သော ကွက်လပ်မှာ ၁.၃၂s ချန်ခဲ့
#      · **အချိုး** ဖြစ်၍ မူရင်းရဲ့ ကွက်လပ် ဖြန့်ကျဲမှုပေါ် မူတည်ကာ
#        ဖိုင်တိုင်း အဓိပ္ပာယ် မတူ — ချိန်ဖို့ ဗီဒီယို အများကြီး လိုခဲ့
#    ⇒ ယခု `keep_pause` က **ကိန်းသေ** ဖြစ်ပြီး ချန်လိုက်တဲ့ ကွက်လပ်ရဲ့
#      p90 က `keep_pause` ကိုယ်တိုင် ⇒ reference နဲ့ ကိုက်ချင်လျှင်
#      အဲဒီ ကိန်းကို ထားရုံပဲ (ပစ်မှတ် ၀.၅၆s)。
#    ⚠️ recipe ကိန်းတွေကို **ဖြုတ်မှု ပမာဏ မပြောင်းအောင်** ပြန်ချိန်ထားသည်
#      (preset တိုင်း ±၀.၁ မှတ် · ဖြတ်ချက်က လျော့သွား — no-op ဖြတ်ချက်
#      ပျောက်၍: ref-fast ၅၃→၃၁ · short-916 ၄၃→၂၇)。
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
        # ⚠️ ချန်ရမည့် အရှည် = `keep_pause` **ကိန်းသေ** (အထက် မှတ်ချက်)。
        #    「min_sil ထက် ရှည်တဲ့ ကွက်လပ်ကို keep_pause ဖြစ်အောင် လျှော့」。
        _h = keep_pause / 2.0
        ca = a + _h; cb = b - _h                    # ⚠️ တိတ်ဆိတ်မှု **အထဲက** ယူ
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
    # ⚠️⚠️ **သုံးစွဲသူ ဖတ်ရသော စာ ဖြစ်ရမည်**。 「F2 ဖြတ်မှတ် ၃ ခု
    #    စကားပေါ် ကျသည်」 ဆိုတာ customer အတွက် လုပ်စရာ မပြပါ — ကုတ် နာမည်
    #    (F2/F3) က support အတွက်、ကျန်တာက **ဘာဖြစ်လဲ + ဘာလုပ်ရမလဲ**。
    #    ဂိတ်ကို **မလျှော့ပါ** — F2/F3 က ထုတ်ခွင့် ပိတ်ဆဲ (product ရဲ့ ကတိ:
    #    စကားထဲ ဘယ်တော့မှ မဖြတ်)。 စာသားသာ ပြင်သည် (၂၀၂၆-၁၀-၀၁)。
    if bad:
        refus.append(
            f"F2 — ဖြတ်မှတ် {len(bad)} ခု စကားသံပေါ် ကျနေသည် ⇒ စကားလုံး "
            f"ပြတ်မည်ဖြစ်၍ မထုတ်ပါ။ 「ဖြတ်မှု」 ကို 「ညင်သာ」 သို့မဟုတ် "
            f"「မဖြတ်ပါ」 နဲ့ ပြန်စမ်းပါ")
    if short:
        refus.append(
            f"F3 — ဖြတ်ပြီး ကျန်သော အပိုင်း {len(short)} ခု တိုလွန်းသည် "
            f"({min(short):.2f}s) ⇒ ခုန်နေမည်ဖြစ်၍ မထုတ်ပါ။ 「ဖြတ်မှု」 ကို "
            f"ပိုညင်သာစွာ ထားပါ (တိတ်ဆိတ်မှု အနည်းဆုံး ကို တင်ပါ)")
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


# ══ ဖျက်ချက်ကို အသံရဲ့ အဆုံးထိ ချဲ့ခြင်း ═══════════════════════════
# ⚠️⚠️ ၂၀၂၆-၁၀-၀၃ Zin: 「cut engine လုံး၀ အဆင်မပြေ · စကားလုံး ပြတ်/ပျောက် ·
#    ရွေးထားတဲ့ ဖျက်ချက် မမှန်」。 တကယ့် transcript (ဝါကျ ၃၁ · ၁၇၈.၇s) နဲ့ —
#      ချဲ့မှု မရှိ  : overcut max ၀.၀၂၀s · leftover max ၀.၃၂၀s · ၆/၃၁
#    ဖျက်ချက်က စောစော ရပ်ပြီး ဝါကျရဲ့ အမြီး ကျန်သည် — နားထောင်ရင်
#    「စကားလုံး ပြတ်」 လိုပဲ ကြားရသဖြင့် လက္ခဏာ ၂ ခု ဖြစ်နေခဲ့。
#
# ⚠️⚠️⚠️ **ပုံသေ `cap` နဲ့ မရ** (ပထမ ရေးချက် — ပိုဆိုးသွားခဲ့သည်):
#    cap ၀.၄၀s က **ဘေးဝါကျ ဘယ်မှာလဲ မကြည့်**သဖြင့် ဝါကျတွေ ကပ်နေတဲ့အခါ
#    နောက်ဝါကျရဲ့ အစကို ဖြတ်မိသည် — overcut max **၀.၇၆၀s · ၉/၃၁**。
#    ဝါကျကြား ကွက်လပ်က **၅/၃၀ မှာ ၀.၁၀s အောက်** ဖြစ်၍ ကပ်နေတာ ပုံမှန်。
#    ⇒ **ဘေးဝါကျရဲ့ နယ်နိမိတ်နဲ့ ကန့်သတ်**ရမည် — အဲဒါ သိပြီးသား。
#
# ⚠️ ဘောင် နှိုင်းယှဉ်ချက် (တကယ့် ကုဒ်လမ်းကြောင်းနဲ့ တိုင်း):
#      ချဲ့မှု မရှိ        overcut max ၀.၀၂၀ · leftover max ၀.၃၂၀ · ၆/၃၁
#      ပုံသေ cap ၀.၄၀     overcut max **၀.၇၆၀** · leftover max ၀.၀၆၀ · ၉/၃၁
#      **ဘေးဝါကျ ကန့်**   overcut max ၀.၀၆၀ · leftover max ၀.၀၈၀ · **၅/၃၁**
#    ပြီးတော့ `tol` ၀.၀၆–၀.၄၀ အားလုံး **ရလဒ် တူညီ** — ဘောင်က အလုပ်လုပ်တာ
#    ဖြစ်ပြီး tol က မဟုတ် ⇒ ခိုင်မာသော ဒီဇိုင်း。
#
# ⚠️ ကျန် ၅ ခု (၀.၀၆–၀.၀၈s) က **frame ၂၀ms grid ရဲ့ ကိုယ်ပိုင် အမှား**
#    ဖြစ်သည် — ၁၀ms နဲ့ တိုင်းလျှင် **၀/၃၁**。 ⇒ ချဲ့ချက်အတွက်
#    သိမ်မွေ့သော track ပေးရန် (worker က `analyse(wav, frame=0.010)`)。
GROW_TOL = 0.16         # ⚠️ ၀.၀၆–၀.၄၀ ရလဒ် တူ ⇒ အလယ်အလတ် ယူသည်
GROW_NEAR_DB = 14.0
GROW_FRAME = 0.010      # ⚠️ ၂၀ms ဆို ၅/၃၁ ကျန် · ၁၀ms ဆို သိသိသာသာ နည်း
# ⚠️⚠️ **「စကားလုံး အလယ်မှာ မရပ်ရ」 စည်းမျဉ်း ကို စမ်းပြီး ပယ်သည်** —
#    ဘောင်မှာ အသံ ဆက်နေလျှင် စကားလုံး အဆုံးထိ ယူကြည့်ရာ ပိုဆိုးသွားသည်
#    (၂/၃၁ → ၆/၃၁ · overcut max ၀.၃၅s)。 အကြောင်းရင်း — မြန်မာစကားမှာ
#    အသံထွက်မှုက **ဝါကျကြားမှာလည်း ဆက်နေ**သဖြင့် 「အသံ ဆက်နေ = စကားလုံး
#    တစ်လုံးတည်း」 မဟုတ်。 ဘောင် ၀.၀၄–၀.၃၀ အားလုံး ပိုဆိုးသည်。


# ⚠️⚠️ **နယ်နိမိတ်ကို mark စာရင်းကနေ မှန်းလို့ မရ**。 ဝါကျ ကပ်နေလျှင်
#    `segs[i-1].end == segs[i].start` ဖြစ်၍ **တန်ဖိုး တူညီ**သည် ⇒
#    「ရှေ့ဝါကျရဲ့ အဆုံး」 နဲ့ 「ဒီဝါကျရဲ့ အစ」 ကို ကိန်းနဲ့ မခွဲနိုင်。
#    တင်းတင်း `<` သုံးခဲ့ရာ **ဝါကျ ၂ ခု ကျော်** နောက်ပြန် ဆွဲမိပြီး
#    overcut max **၁.၃၅၀s** ဖြစ်ခဲ့သည် (တကယ့် ကုဒ်လမ်းကြောင်းနဲ့ တိုင်း)。
#    ⇒ ခေါ်သူက နယ်နိမိတ်ကို **တိုက်ရိုက် ပေး**ရမည် (`bounds`)。


def grow_to_speech(a, b, db, hop, dur, lo=None, hi=None,
                   tol=GROW_TOL, near=GROW_NEAR_DB):
    """ဖျက်ချက် `[a,b]` ကို **အသံ ဆက်နေသမျှ** ချဲ့သည် — `[lo,hi]` အတွင်းသာ

    ⚠️ `db` မပါလျှင် **ဘာမှ မလုပ်** — မှန်းဆ မချဲ့ရ。
    ⚠️ `lo`/`hi` မပါလျှင် **မချဲ့ပါ** — ပုံသေ cap က နောက်ဝါကျကို
       မျိုခဲ့သည် (overcut max ၀.၇၆s)。 နယ်နိမိတ် မသိဘဲ မချဲ့ရ。
    ⚠️ ဘယ်တော့မှ **မကျုံ့ရ** — ကျုံ့လျှင် ဖျက်ခိုင်းထားတာ ကျန်မည်。
    """
    import numpy as _np
    a = float(a); b = float(b)
    if db is None or hop is None or not len(db) or lo is None or hi is None:
        return a, b
    lo = max(0.0, float(lo)); hi = min(float(dur), float(hi))
    if hi <= lo:
        return a, b
    floor = float(_np.percentile(db, 90)) - float(near)
    voiced = db >= floor
    n = len(voiced)
    ta = max(1, int(float(tol) / float(hop)))
    # ── အဆုံးကို ရှေ့ဆက် — `hi` ကျော်လို့ မရ ──
    j = min(n, max(0, int(b / float(hop))))
    jm = min(n, max(0, int(hi / float(hop))))
    while j < jm:
        nxt = voiced[j:min(jm, j + ta + 1)]
        if not nxt.any():
            break
        j += int(_np.nonzero(nxt)[0][-1]) + 1
    b2 = min(hi, j * float(hop))
    # ── အစကို နောက်ပြန် — `lo` ကျော်လို့ မရ ──
    i = min(n, max(0, int(a / float(hop))))
    im = max(0, int(lo / float(hop)))
    while i > im:
        prv = voiced[max(im, i - ta - 1):i]
        if not prv.any():
            break
        i -= (len(prv) - 1 - int(_np.nonzero(prv)[0][0])) + 1
    a2 = max(lo, i * float(hop))
    return min(a2, a), max(b2, b)


def subtract(spans, drop, sil=None, snap=0.35, min_keep=MIN_KEEP_RUN,
             db=None, hop=None, bounds=None, gdb=None, ghop=None, dur=None):
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
    def _gap_silent(x, y):
        """`[x, y]` **တစ်ခုလုံး** တိတ်ဆိတ်မှုထဲ ရှိလား

        ⚠️⚠️ **အမှတ် တစ်ခုတည်း စစ်လို့ မရ**。 ပထမ ရေးချက်မှာ ဆွဲသွားမည့်
           အမှတ်ကိုသာ စစ်ခဲ့ရာ ကိန်း **လုံးဝ မပြောင်း**ခဲ့သည် — တိတ်ဆိတ်မှု
           တစ်ခုရဲ့ **အနားသတ်** က အမြဲ 「တိတ်ဆိတ်မှုထဲ」 ဖြစ်ပြီး အဲဒီ
           အနားသတ်ကနေ တောင်းချက်အထိ ကြားမှာ စကား ရှိနေနိုင်သည်
           (ဥပမာ တောင်းချက် ၁၀.၀ · တိတ်ဆိတ်မှု အဆုံး ၉.၇ ⇒ ၀.၃s စကား ပါသွား)。
        """
        if y < x:
            x, y = y, x
        if y - x <= 1e-6:
            return True
        return any(a0 - 1e-6 <= x and y <= b0 + 1e-6 for a0, b0 in (sil or []))

    def snapto(t, lo, hi, req_a, req_b, want_dir):
        """`t` ကို ဆွဲသည် — ⚠️ **တောင်းချက် ပြင်ပသို့ ကျယ်လျှင်
        တိတ်ဆိတ်မှုထဲ ဖြစ်မှသာ** ခွင့်ပြုသည်。

        ⚠️⚠️ ၂၀၂၆-၁၀-၀၂ တိုင်းချက် — ယခင် ရေးချက်က ဘယ်/ညာ `±snap`
           အထိ ကန့်သတ်မရှိ ကျယ်ခွင့် ပေးထားသဖြင့် ဝါကျအလယ်မှာ ဖျက်လျှင်
           **ဘေးက စကား ပါသွား**သည်:
             ဖျက် ၀.၄s ⇒ အပို စကား အလယ် **၀.၂၂s** (၃၀/၅၁ ခုမှာ ဖြစ်)
             ဖျက် ၀.၉s ⇒ p90 **၀.၅၆s** · အများဆုံး ၀.၆၆s (၂၇/၃၀)
           မြန်မာစာ အမြန်နှုန်းနဲ့ဆို **စကားလုံး တစ်လုံးစာ** ဖြစ်သည်。
           Zin: 「user ရွေးလိုက်တဲ့ ဖျက်ချက်တစ်ခုချင်းစီကို သေချာ ဖြတ်ပေးနိုင်ဖို့
           အရမ်းအရေးကြီးတယ်」 ⇒ တောင်းချက်ထက် **ပို၍ မဖျက်ရ**。
        ⚠️ တိတ်ဆိတ်မှုထဲ ကျယ်တာကတော့ ခွင့်ပြုသည် — အသံ မပါသဖြင့်
           ဆုံးရှုံးစရာ မရှိပြီး ဖြတ်မှတ်က ပိုညင်သာသည်。
        """
        cands = []
        if edges:
            for e in edges:
                if abs(e - t) <= snap and lo <= e <= hi:
                    cands.append(e)
        q = quiet_at(t, db, hop, snap)
        if lo <= q <= hi:
            cands.append(q)
        # ⚠️⚠️ **ကျုံ့တာထက် ကျယ်တာ သာသည်**。 တောင်းချက် အတွင်းသို့ ဆွဲလျှင်
        #    ဖျက်ခိုင်းထားတာ တစ်စိတ်တစ်ပိုင်း **မဖျက်ဖြစ်ဘဲ ကျန်**မည် (Zin ရဲ့
        #    「၁၀၀% ဖျက်」 စည်းကို ချိုးဖောက်သည်)。 ပြင်ပသို့ ကျယ်တာကတော့
        #    အောက်က စစ်ချက်က တိတ်ဆိတ်မှုဖြစ်မှ ခွင့်ပြုသဖြင့် အသံ မဆုံးရှုံးပါ。
        #    ဥပမာ — တောင်းချက် ၅.၁၀ · တိတ်ဆိတ်မှု ၄.၇၀–၅.၃၀ ဆိုလျှင်
        #    ၅.၃၀ (ကျုံ့) ထက် ၄.၇၀ (ကျယ်) က မှန်သည်。
        cands.sort(key=lambda c: (0 if (c - t) * want_dir >= -1e-6 else 1,
                                  abs(c - t)))
        for c in cands:
            if c < req_a - 1e-6:                 # ဘယ်ဘက် ကျယ်
                if not _gap_silent(c, req_a):
                    continue
            elif c > req_b + 1e-6:               # ညာဘက် ကျယ်
                if not _gap_silent(req_b, c):
                    continue
            return c
        return t
    cuts = []
    _dur = float(dur) if dur else (max(b for _a0, b in spans) if spans else 0.0)
    # ⚠️ `bounds` က `drop` နဲ့ **အတန်းတူ** ဖြစ်ရမည် ⇒ အတူတွဲ၍ စဉ်သည်
    _bd = list(bounds) if bounds else [None] * len(list(drop))
    _pairs = sorted(zip(list(drop), _bd), key=lambda z: (float(z[0][0]), float(z[0][1])))
    for (a, b), _bnd in _pairs:
        _a, _b = float(a), float(b)
        # ⚠️⚠️ **အရင်ဆုံး အသံရဲ့ အဆုံးထိ ချဲ့ရမည်** — မချဲ့လျှင် ဝါကျရဲ့
        #    အမြီး ကျန်ပြီး 「ဖျက်ပေမယ့် မပျောက်」 ဖြစ်မည်。
        # ⚠️ `marks` (ဝါကျ နယ်နိမိတ်များ) **မပါလျှင် မချဲ့ပါ** — နယ်နိမိတ်
        #    မသိဘဲ ချဲ့လျှင် နောက်ဝါကျကို မျိုမည် (overcut max ၀.၇၆s တိုင်းထား)。
        # ⚠️ `gdb`/`ghop` = **သိမ်မွေ့သော** track (၁၀ms)。 မပါလျှင် `db` သုံးသည်
        #    — ၂၀ms ဆို ကျန် ၅/၃၁ · ၁၀ms ဆို ၀/၃၁。
        _lo = _hi = None
        if _bnd is not None:
            _gd = gdb if gdb is not None else db
            _gh = ghop if ghop else hop
            _lo, _hi = float(_bnd[0]), float(_bnd[1])
            _a, _b = grow_to_speech(_a, _b, _gd, _gh, _dur, lo=_lo, hi=_hi)
        # ⚠️ အစက **စောစော** (−၁) · အဆုံးက **နောက်ကျကျ** (+၁) ဘက် ဦးစားပေး
        # ⚠️⚠️ snap ကိုပါ **နယ်နိမိတ်နဲ့ ကန့်သတ်**ရမည်。 မကန့်သတ်လျှင်
        #    ချဲ့ချက်ကို ဂရုစိုက်ပြီး ဘောင်ထဲ ထားပေမယ့် snap က ပြန်ကျော်ပြီး
        #    ဘေးဝါကျကို ဖြတ်မိမည် — တကယ် ဖြစ်ခဲ့: overcut max **၁.၃၅၀s**。
        _sl = _a - snap if _lo is None else max(_lo, _a - snap)
        _sh = _b + snap if _hi is None else min(_hi, _b + snap)
        a2 = snapto(_a, _sl, _b, _a, _b, -1)
        b2 = snapto(_b, _a, _sh, _a, _b, +1)
        # ⚠️⚠️ **ဘယ်တော့မှ မကျုံ့ရ**。 `snapto` က ဦးစားပေး ဘက်မှာ ရွေးစရာ
        #    မရှိလျှင် **တစ်ဖက်ကို** ယူပြီး တောင်းချက် အတွင်းသို့ ဝင်သွားသည်
        #    ⇒ ဖျက်ခိုင်းထားတာ ကျန်မည် (Zin ရဲ့ 「၁၀၀% ဖျက်」 ကို ချိုး)。
        #    တကယ် ဖြစ်ခဲ့ — ဝါကျ ၂ ခုမှာ ၀.၀၆s ကျန်ခဲ့ပြီး အဲဒါက
        #    ကျန်သေးသော အမှား **အားလုံး** ဖြစ်သည် (၂/၃၁ → ၀/၃၁)。
        if a2 > _a: a2 = _a
        if b2 < _b: b2 = _b
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


# ══ visible-shot stabilizer ══════════════════════════════════════════
# A cut engine may quite correctly preserve a 300 ms spoken fragment: deleting
# it would change what the user said.  A delivered video must nevertheless not
# flash a 300 ms shot.  Do not solve that conflict by dropping or merging words.
# Instead, restore a small amount of *adjacent source* around the fragment.  An
# explicit user drop is an absolute fence and is never crossed.
VISUAL_MIN_SHOT = 0.60
VISUAL_TARGET_SHOT = 0.80
VISUAL_EPS = 0.001


def stabilize_visible_spans(spans, explicit_drops=None, dur=None,
                            minimum=VISUAL_MIN_SHOT,
                            target=VISUAL_TARGET_SHOT):
    """Return visible-safe spans without deleting a kept spoken fragment.

    ``spans`` are the currently kept source ranges.  If one is shorter than
    ``minimum``, we symmetrically re-add surrounding source up to ``target``.
    Only engine-removed context may be restored; ranges in ``explicit_drops``
    were chosen by the user and form hard boundaries.  A fragment that cannot
    reach the delivery floor is returned in ``blocked`` for Cut Review rather
    than silently changed.

    Returns ``(clean, stabilized, blocked)``.  ``stabilized`` is audit data
    suitable for the cut-preview UI.  No speech/text is removed or reordered.
    """
    try:
        limit = max(0.0, float(dur)) if dur is not None else None
    except (TypeError, ValueError):
        limit = None
    floor = max(0.05, float(minimum))
    aim = max(floor, float(target))

    kept = []
    for raw in (spans or []):
        try:
            a, b = float(raw[0]), float(raw[1])
        except (TypeError, ValueError, IndexError):
            continue
        if limit is not None:
            a, b = max(0.0, a), min(limit, b)
        if b - a > 0.05:
            kept.append((a, b))
    kept.sort()

    fences = []
    for raw in (explicit_drops or []):
        try:
            a, b = float(raw[0]), float(raw[1])
        except (TypeError, ValueError, IndexError):
            continue
        if b > a:
            fences.append((max(0.0, a), min(limit, b) if limit is not None else b))
    fences.sort()

    def bounds(a, b):
        """Nearest user-selected deletion on either side of a kept range."""
        lo, hi = 0.0, (limit if limit is not None else float("inf"))
        for x, y in fences:
            if y <= a + VISUAL_EPS:
                lo = max(lo, y)
            elif x >= b - VISUAL_EPS:
                hi = min(hi, x)
            elif x < b and y > a:
                # A malformed keep/drop overlap must not be repaired by
                # extending through the user's exact deletion.
                lo, hi = a, b
        return lo, hi

    out, stabilized, blocked = [], [], []
    for a, b in kept:
        old = b - a
        if old + VISUAL_EPS >= floor:
            out.append((a, b)); continue
        lo, hi = bounds(a, b)
        need = max(0.0, aim - old)
        before_cap, after_cap = max(0.0, a - lo), max(0.0, hi - b)
        before = min(before_cap, need / 2.0)
        after = min(after_cap, need - before)
        remain = need - before - after
        if remain > VISUAL_EPS:
            extra = min(before_cap - before, remain)
            before += max(0.0, extra); remain -= max(0.0, extra)
        if remain > VISUAL_EPS:
            extra = min(after_cap - after, remain)
            after += max(0.0, extra)
        aa, bb = a - before, b + after
        new_d = bb - aa
        if new_d + VISUAL_EPS < floor:
            out.append((a, b))
            blocked.append(dict(start=round(a, 3), end=round(b, 3),
                                dur=round(old, 3), max_dur=round(new_d, 3)))
            continue
        out.append((aa, bb))
        stabilized.append(dict(start=round(a, 3), end=round(b, 3),
                               before=round(old, 3),
                               after=round(new_d, 3)))

    # Padding can touch a neighbouring kept run.  Coalesce it: this restores
    # source continuity and avoids creating two adjacent visual cuts.
    clean = []
    for a, b in out:
        if clean and a <= clean[-1][1] + VISUAL_EPS:
            clean[-1] = (clean[-1][0], max(clean[-1][1], b))
        else:
            clean.append((a, b))
    return clean, stabilized, blocked


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


# ══════════════════════════════════════════════════════════════════════
# ချန်ထားပြီး **ဝါကျ မရှိသော** အပိုင်းများ (၂၀၂၆-၀၉-၂၂ Zin)
# ══════════════════════════════════════════════════════════════════════
# ⚠️ **ဤဟာက ဖုံးကွယ်ခဲ့သော အပေါက်**。 Script Editor က (၁) ဝါကျများ နှင့်
#    (၂) engine **ဖြတ်ပစ်လိုက်သော** တိတ်ဆိတ်မှုများ ကိုသာ ပြခဲ့သည်。
#    ⇒ 「ချန်ထားပြီး ဝါကျ မရှိသော အသံ」က row တစ်ခုမှ မဖြစ်ဘဲ **လုံးဝ
#      မမြင်ရ** — သုံးစွဲသူ ဖျက်လို့ မရဘဲ ထွက်ချက်ထဲ ပါသွားသည်。
#    တိုင်းချက် (j_58639d6961da): ထွက်ချက် ၆၉.၅s ရဲ့ **၁၂.၆s (၁၈%)** က
#    Script Editor မှာ တစ်ခါမှ မပေါ်ခဲ့သော ပိုင်းများ ဖြစ်ခဲ့သည် —
#    out 0:30–0:32 · 0:40–0:45 · 1:03–1:07 (Zin ပြောသည့် နေရာ အတိအကျ)。
# ⚠️ Zin ရဲ့ စည်းကမ်း: 「ဖြတ်ရတာ ခက်ရင် မဖြတ်နဲ့ · user ကို အသံလိုင်းနဲ့ ပြပေး ·
#    သူ ကိုယ်တိုင် နားထောင်ပြီးမှ ဖြတ်မယ်」 ⇒ ဤ function က **မဖြတ်ပါ**。
#    ပြရန် စာရင်းသာ ထုတ်သည် — ဆုံးဖြတ်ချက်က သုံးစွဲသူ့ဟာ。
UNL_MIN = 0.25       # ဤထက် တိုလျှင် row မပြ (ဖတ်ရ မရ ဖြစ်မည်)
UNL_PAD = 0.30       # ဝါကျ နယ်နိမိတ် ဝန်းကျင် လျှော့ — ASR အချိန် အနည်းငယ် လွဲသည်


UNL_GAP = 0.80       # ဤထက် နီးသော အပိုင်းအစများကို **တစ်ကြောင်းတည်း** ပေါင်း


def unlisted(spans, segs, dur, meas=None, min_d=UNL_MIN, pad=UNL_PAD,
             merge_gap=UNL_GAP):
    """ချန်ထားသော အပိုင်းထဲက **ဝါကျ မရှိသော** ပိုင်းများ。

    `spans` = ချန်မည့် (a,b) များ · `segs` = ASR ဝါကျများ · `meas` =
    `measure.speech()` ရဲ့ ရလဒ် (ပါလျှင် စကား ဘယ်လောက် ပါလဲ ပါ တိုင်းသည်)。

    ⇒ `[{a, b, dur, speech, kind}]` — `kind`: `"speech"` (စကား ပါ · အရေးကြီး) ·
      `"quiet"` (တိတ်ဆိတ်) · `"mixed"`。
    """
    if not spans: return []
    # ── ဝါကျ နယ်နိမိတ်များ (pad နဲ့ ကျယ်) ──
    sent = []
    for s in (segs or []):
        try: a, b = float(s.get("start")), float(s.get("end"))
        except (TypeError, ValueError): continue
        if b > a: sent.append((a - pad, b + pad))
    sent.sort()
    # merge
    mg = []
    for a, b in sent:
        if mg and a <= mg[-1][1]: mg[-1][1] = max(mg[-1][1], b)
        else: mg.append([a, b])
    # ── span တစ်ခုချင်းကနေ ဝါကျ နယ်များ ဖြုတ် ──
    out = []
    for a, b in spans:
        try: a, b = float(a), float(b)
        except (TypeError, ValueError): continue
        cur = [[a, b]]
        for sa, sb in mg:
            nxt = []
            for x, y in cur:
                if sb <= x or sa >= y: nxt.append([x, y]); continue
                if sa > x: nxt.append([x, min(sa, y)])
                if sb < y: nxt.append([max(sb, x), y])
            cur = [p for p in nxt if p[1] - p[0] > 1e-6]
        out.extend(cur)
    # ── စကား ပါမပါ တိုင်း ──
    runs = []
    if meas:
        try: runs = [(float(x), float(y)) for x, y in (meas[0] or [])]
        except Exception: runs = []
    res = []
    for x, y in out:
        d = y - x
        if d < min_d: continue
        sps = sum(max(0.0, min(y, q) - max(x, p)) for p, q in runs) if runs else None
        if sps is None: kind = "unknown"
        elif sps >= max(0.35, 0.25 * d): kind = "speech"
        elif sps <= 0.05: kind = "quiet"
        else: kind = "mixed"
        res.append(dict(a=round(x, 2), b=round(y, 2), dur=round(d, 2),
                        speech=(None if sps is None else round(sps, 2)),
                        kind=kind))
    res.sort(key=lambda r: r["a"])
    # ── နီးစပ်သော အပိုင်းအစများ ပေါင်း ──
    # ⚠️ တိုင်းချက်မှာ ၀.၃၂s အပိုင်းအစ ၁၀ ခု ထွက်ခဲ့သည် — တစ်ခုချင်း row
    #    ပြလျှင် ဖတ်ရ မရ。 သုံးစွဲသူကလည်း 「တစ်နေရာ」ဟုသာ ခံစားသည်
    #    (Zin: 「0:40 ကနေ 0:44 တစ်နေရာ」) ⇒ ပေါင်းပြသည်。
    mrg = []
    for r in res:
        if mrg and r["a"] - mrg[-1]["b"] <= merge_gap:
            p_ = mrg[-1]
            p_["b"] = r["b"]; p_["dur"] = round(p_["b"] - p_["a"], 2)
            if p_.get("speech") is not None and r.get("speech") is not None:
                p_["speech"] = round(p_["speech"] + r["speech"], 2)
            # ⚠️ စကား ပါသော ပိုင်း တစ်ခု ပါလျှင် တစ်ခုလုံးကို စကား အဖြစ် ပြရမည်
            if r["kind"] == "speech" or p_["kind"] == "speech": p_["kind"] = "speech"
            elif "unknown" in (r["kind"], p_["kind"]): p_["kind"] = "unknown"
            elif "mixed" in (r["kind"], p_["kind"]): p_["kind"] = "mixed"
        else:
            mrg.append(dict(r))
    return [r for r in mrg if r["dur"] >= min_d]


# ══ ဖြတ်ချက် စစ်ဆေးမှု — **mask ကို မယုံဘဲ** ════════════════════
# ⚠️⚠️ **ဘာကြောင့် လိုလဲ** — `in_speech` စစ်ချက်က `measure.speech()` ရဲ့
#    mask နဲ့ စစ်ပြီး、ဖြတ်မှတ် ချတဲ့ engine ကလည်း **အဲဒီ mask အတိုင်းပဲ**
#    ဖြတ်သည်。 ⇒ mask က စကားကို လွတ်သွားလျှင် engine က ဖြတ်မိပြီး
#    စစ်ချက်ကလည်း 「တိတ်ဆိတ်မှုပဲ」 ဟု အတည်ပြုမည် —
#    **ဘယ်တော့မှ မကျနိုင်သော စစ်ချက်** (ikki-measure-the-real-path)。
#    s6 မှာ `cut_in_speech=0` · `စကားထဲ 0/86` ဟု ပြပါလျက် ဖြုတ်ချက်တွေကို
#    သီးခြား တိုင်းကြည့်ဖို့ လမ်း မရှိခဲ့。
#
# ⚠️ ဒီနည်းက **ဆုံးဖြတ်နည်း မတူ**: mask မသုံး · voice ratio မသုံး ·
#    smoothing မသုံး。 「စကားအဆင့်」 ကို **ချန်ထားသော** အပိုင်းတွေရဲ့
#    p90 ကနေ ယူသည် (mask ကနေ မဟုတ်)。 decode ကတော့ ffmpeg အတူတူ —
#    အမှားက decode မှာ မဟုတ်ဘဲ threshold/voice/smoothing မှာ ဖြစ်၍。
#
# ⚠️ **ဂိတ် မလုပ်သေး** — ဖိုင် ၁ ခုကနေ ဘောင် မချရ
#    (measure-distribution-rule)。 ကိန်း တင်ပြရုံသာ。 ဖိုင် အများနဲ့
#    တိုင်းပြီးမှ ဘောင် ချရမည် — ဘယ်သူ ဘယ်ဟာကို ပိတ်မလဲ Zin ဆုံးဖြတ်ရန်。
LOUD_NEAR_DB = 14.0     # စကားအဆင့် (p90) ကနေ အောက် ဘယ်လောက်ထိ 「ကျယ်」
LOUD_FRAC = 0.50        # တိုင်းချက်: စကား p5 ၀.၆၈ · တိတ် p95 ၀.၁၁ ⇒ ကြားထဲ
LOUD_MIN = 0.12         # ဒီထက် တိုလျှင် ကလစ်သံ · စကား မဟုတ်
# ⚠️⚠️ **အဆင့်တစ်ခုတည်းနဲ့ မရ** (၂၀၂၆-၁၀-၀၃)。 s7 မှာ ၁၆၆.၁၉–၁၆၆.၆၁s ကို
#    「ကျယ်သံ ဖြုတ်မိ」 ဟု သတိပေးခဲ့ရာ တကယ်က **အသက်ရှူသံ** ဖြစ်သည် —
#    voice ratio (၃၀၀–၃၄၀၀Hz အချိုး) med **၀.၁၂၃** ဖြစ်ပြီး ဘေးက တကယ့်
#    စကားက ၀.၅၁–၀.၆၈。 mask က မှန်ကန်စွာ ဖြတ်ခဲ့ပြီး ကျွန်တော့် စစ်ချက်က
#    မှားစွပ်စွဲခဲ့သည် (သုံးစွဲသူကို 「စကားလုံး ပြတ်」 ဟု အချက်ပြမိမည်)。
# ⚠️ ဒါပေမယ့် mask ရဲ့ **ကိန်းသေ ၀.၂၅ ကို ပြန်မသုံးရ** — သုံးလျှင်
#    စစ်ချက်က mask နဲ့ တူသွားပြီး ပြန်ကန်းမည် (ikki-cut-check-blind)。
#    ⇒ **အချိုးနဲ့** ကြည့်သည်: ဒီဖိုင်ရဲ့ စကား voice median နဲ့ နှိုင်းပြီး
#      ထက်ဝက် မမီလျှင် စကား မဟုတ် (၀.၁၂၃/၀.၆၅၄ = ၀.၁၉ ⇒ မဟုတ်)。
VERIFY_VOICE_REL = 0.50



def loud_removed(wav, spans, dur, near=LOUD_NEAR_DB,
                 frac=LOUD_FRAC, mind=LOUD_MIN, vrel=VERIFY_VOICE_REL):
    """ဖြုတ်လိုက်သော အသံထဲ **ကျယ်သော အသံ** ဘယ်လောက် ပါလဲ

    (total_s, pct, regions) ပြန်သည်。 `regions` = ဂိတ် ကျော်သော
    (start, end, frac, loud_s, max_db) စာရင်း。

    ⚠️ `spans` က **နောက်ဆုံး** ချန်ထားချက် ဖြစ်ရမည် — engine ဖြတ်ချက် ·
       auto-clean · သုံးစွဲသူ ဖျက်ချက် အားလုံး ပြီးမှ。 engine ဖြတ်ချက်
       တစ်ခုတည်းကို စစ်လျှင် auto-clean လမ်းကြောင်း လွတ်သွားမည် —
       အဲဒါက `in_speech` စစ်ချက် လွတ်ခဲ့သော လမ်းကြောင်း အတိအကျ
       (worker/run.py ရဲ့ ZJL စည်းမျဉ်း ⑧ မှတ်ချက်)。
    ⚠️ ကျဆုံးလျှင် **အလုပ် မရပ်ရ** — တိုင်းချက် မရတာက render မထွက်ရ
       လောက်အောင် မဟုတ်。 `None` ပြန်သည်。
    """
    import subprocess as _sp
    try:
        import numpy as _np
        raw = _sp.run(["ffmpeg", "-v", "error", "-i", wav, "-ac", "1",
                       "-ar", "16000", "-f", "f32le", "-"],
                      capture_output=True).stdout
        x = _np.frombuffer(raw, _np.float32)
        h = int(16000 * M.FRAME)
        n = len(x) // h
        if n < 10:
            return None
        fr = x[:n * h].reshape(n, h)
        db = 20 * _np.log10(_np.sqrt((fr ** 2).mean(1) + 1e-12) + 1e-12)
        # ⚠️⚠️ **အသံရဲ့ သဘာဝကိုပါ ကြည့်ရမည်** — အဆင့်တစ်ခုတည်းနဲ့ ဆိုလျှင်
        #    အသက်ရှူသံကို 「စကားလုံး ပြတ်」 ဟု မှားစွပ်စွဲမည် (s7 ၁၆၆.၂s)。
        #    ၃၀၀–၃၄၀၀Hz အချိုး — `measure.analyse` နဲ့ တူညီသော တွက်နည်း
        #    ဖြစ်သော်လည် **ဂိတ်က မတူ** (mask က ကိန်းသေ ၀.၂၅ · ဒီမှာ
        #    ဖိုင်ရဲ့ ကိုယ်ပိုင် စကား median နဲ့ **အချိုး**)。
        _F = _np.abs(_np.fft.rfft(fr * _np.hanning(h), axis=1))
        _f = _np.fft.rfftfreq(h, 1.0 / 16000)
        vo = _F[:, (_f >= 300) & (_f <= 3400)].sum(1) / (_F.sum(1) + 1e-9)
        kept = _np.zeros(n, bool)
        for a, b in (spans or []):
            kept[int(float(a) / M.FRAME):int(float(b) / M.FRAME)] = True
        if not kept.any():
            return None
        floor = float(_np.percentile(db[kept], 90)) - float(near)
        # ⚠️ 「စကား」 ရဲ့ voice median — **ဒီဖိုင်ကနေ** ယူသည် (ကိန်းသေ မဟုတ်)。
        #    ချန်ထားချက်ထဲ အဆင့် မြင့်သော frame တွေကို စကား ဟု ယူသည်。
        _spk = kept & (db >= floor)
        vmed = float(_np.median(vo[_spk])) if _spk.any() else 0.0
        vmin = vmed * float(vrel)
        # ── ဖြုတ်လိုက်သော အပိုင်းများ = ချန်ထားချက်ရဲ့ ဖြည့်စွက် ──
        gone, p = [], 0.0
        for a, b in sorted((float(a), float(b)) for a, b in (spans or [])):
            if a - p > 1e-6:
                gone.append((p, a))
            p = max(p, b)
        if float(dur) - p > 1e-6:
            gone.append((p, float(dur)))
        tot = sum(b - a for a, b in gone) or 1e-9
        loud, regions = 0.0, []
        for a, b in gone:
            i0 = int(a / M.FRAME)
            i1 = max(i0 + 1, int(b / M.FRAME))
            seg = db[i0:i1]
            if not len(seg):
                continue
            hot = seg >= floor
            d = float(hot.sum()) * M.FRAME
            loud += d
            f = float(hot.mean())
            # ⚠️ ကျယ်ရုံနဲ့ မလုံလောက် — **စကားနဲ့ တူမှ** သတိပေးရမည်。
            #    s7 ၁၆၆.၂s: ကျယ် ၀.၂၂s ဒါပေမယ့် voice ၀.၁၂၃ (စကား ၀.၆၅)
            #    ⇒ အသက်ရှူသံ ⇒ mask က မှန်ကန်စွာ ဖြတ်ခဲ့သည်。
            _v = float(_np.median(vo[i0:i1][hot])) if hot.any() else 0.0
            if f >= frac and d >= mind and _v >= vmin:
                regions.append((round(a, 2), round(b, 2), round(f, 2),
                                round(d, 2), round(float(seg.max()), 1),
                                round(_v, 3)))
        return dict(loud_s=round(loud, 2),
                    pct=round(100.0 * loud / tot, 1),
                    floor_db=round(floor, 1),
                    voice_med=round(vmed, 3), voice_min=round(vmin, 3),
                    removed_s=round(tot, 2),
                    n=len(regions), regions=regions[:20])
    except Exception:
        return None


# ══ ဖျက်ချက် တစ်ခုချင်း အတည်ပြုခြင်း ═══════════════════════════════
# ⚠️⚠️ Zin ၂၀၂၆-၁၀-၀၃: 「တိကျအောင်လုပ်ပေးဖိ့」。 ယခင် စစ်ချက်က တောင်းချက်နဲ့
#    ချန်ထားချက်ရဲ့ **အချိန် ထပ်မှု**ကိုသာ တိုင်းသည် ⇒ ချို့ယွင်းချက် ၂ ခု:
#      · တိတ်ဆိတ်မှု ကျန်တာကိုပါ 「မဖျက်ဖြစ်」 ဟု သတိပေးသည် (အန္တရာယ် မရှိ)
#      · **ပိုဖြတ်မိမှု လုံးဝ မစစ်** — ဘေးဝါကျရဲ့ စကားလုံး ပါသွားတာက
#        「စကားလုံး ပြတ်」 ဖြစ်ပြီး ပိုဆိုးသည် (Zin ရဲ့ လက္ခဏာ ①)
#    ⇒ **စကား** ကိုသာ တိုင်းပြီး **၂ ဖက်လုံး** စစ်သည်。
# ⚠️ `measure.speech()` ရဲ့ mask ကို **မသုံးရ** — engine က အဲဒါနဲ့ ဖြတ်သဖြင့်
#    စစ်ချက်က ဘယ်တော့မှ မကျနိုင် (ikki-cut-check-blind)。 အဆင့်နဲ့သာ စစ်သည်。
# ⚠️ `VERIFY_FLOOR` = ၀.၀၅၀s。 ၁၀ms grid ကို ၂ ဖက် သုံးရာက လာသော
#    ကိရိယာရဲ့ ကိုယ်ပိုင် ကန့်သတ်ချက် — ဒီအောက်ကို အမှား ဟု မခေါ်နိုင်。
VERIFY_FLOOR = 0.050
VERIFY_NEAR_DB = 14.0


def verify_drops(reqs, spans, gdb, ghop, dur, bounds=None, near=VERIFY_NEAR_DB):
    """ဖျက်ချက် တစ်ခုချင်းကို အတည်ပြု — (kept_speech, cut_outside) စာရင်း

    `kept_speech` = တောင်းချက် **အတွင်း** ကျန်သော စကား (မဖျက်ဖြစ်)
    `cut_outside` = **ဘေးဝါကျရဲ့ စကား** ဖြုတ်မိမှု (စကားလုံး ပြတ်)

    ⚠️⚠️ **တောင်းချက်နဲ့ မတိုင်းရ — ဘောင်နဲ့ တိုင်းရမည်**。 ဝါကျရဲ့ တကယ့်
       အမြီးက `seg.end` ပြင်ပမှာ ရှိတတ်သည် (ဒါက ဖြေရှင်းရမယ့် ပြဿနာ
       ကိုယ်တိုင်)。 တောင်းချက်နဲ့ တိုင်းလျှင် အဲဒီ အမြီးကို ဖြတ်တာကို
       「ပိုဖြတ်မိ」 ဟု မှားခေါ်မည် — မှန်ကန်သော အပြုအမူကို အမှား အဖြစ်
       သတ်မှတ်ရာ ကျသည် (တကယ် ဖြစ်ခဲ့: ဝါကျ ၂၇ မှာ ၀.၁၅s)。
       သုံးစွဲသူ ဂရုစိုက်တာက 「**ငါ့ ဘေးဝါကျကို မထိနဲ့**」 ⇒ ဘောင် ပြင်ပ
       ဖြုတ်မိမှသာ အမှား。 `bounds` မပါလျှင် တောင်းချက်ကို သုံးသည်。
    ⚠️ တိုင်းလို့ မရလျှင် `None` — အလုပ် မရပ်ရ。
    """
    import numpy as _np
    if gdb is None or not ghop or not len(gdb) or not reqs:
        return None
    voiced = gdb >= (float(_np.percentile(gdb, 90)) - float(near))
    n = len(voiced)
    h = float(ghop)

    def _sp(a, b):
        i0 = max(0, int(float(a) / h))
        i1 = min(n, max(i0 + 1, int(float(b) / h)))
        return float(voiced[i0:i1].sum()) * h if i1 > i0 else 0.0

    # ⚠️ ဖြုတ်လိုက်သော အပိုင်းများ = ချန်ထားချက်ရဲ့ ဖြည့်စွက်
    gone, p = [], 0.0
    for a, b in sorted((float(a), float(b)) for a, b in (spans or [])):
        if a - p > 1e-6:
            gone.append((p, a))
        p = max(p, b)
    if float(dur) - p > 1e-6:
        gone.append((p, float(dur)))
    # ⚠️⚠️ ဖျက်ချက် ၂ ခု **ကပ်လျက်** ဖျက်လျှင် တစ်ခုရဲ့ ဖြုတ်ချက်က ကျန်တစ်ခုရဲ့
    #    ဘောင် ပြင်ပမှာ ရှိနေမည် ⇒ တစ်ခုချင်း သီးသန့် စစ်လျှင် **အပြန်အလှန်
    #    အပြစ်တင်**မိပြီး မှားသော သတိပေးချက် ထွက်မည် (တကယ် ဖြစ်ခဲ့:
    #    ၄၆ ခုထဲ ၄ ခု · ပိုဖြတ်မိ max ၂.၇၃s)。 ⇒ **ဘောင် အားလုံး ပေါင်းစု**
    #    ပြင်ပ ဖြုတ်မိမှသာ အမှား。
    _bd = list(bounds) if bounds else [None] * len(list(reqs))
    _allow = []
    for _i, (a, b) in enumerate(reqs):
        _l, _h = float(a), float(b)
        if _i < len(_bd) and _bd[_i] is not None:
            _l, _h = float(_bd[_i][0]), float(_bd[_i][1])
        _allow.append((_l, _h))
    _mrg = []
    for _l, _h in sorted(_allow):
        if _mrg and _l <= _mrg[-1][1] + 1e-6:
            _mrg[-1] = (_mrg[-1][0], max(_mrg[-1][1], _h))
        else:
            _mrg.append((_l, _h))

    def _outside_sp(x, y):
        """`[x,y]` ထဲက စကား — **ခွင့်ပြုထားသော အပိုင်းများ ဖယ်ပြီး**"""
        tot, p = 0.0, float(x)
        for _l, _h in _mrg:
            if _h <= p or _l >= float(y):
                continue
            if _l > p:
                tot += _sp(p, _l)
            p = max(p, _h)
        if p < float(y):
            tot += _sp(p, float(y))
        return tot

    out = []
    for _i, (a, b) in enumerate(reqs):
        a, b = float(a), float(b)
        _lo, _hi = _allow[_i]
        kept = 0.0
        for x, y in (spans or []):
            x, y = float(x), float(y)
            if y <= a or x >= b:
                continue
            kept += _sp(max(x, a), min(y, b))
        # ⚠️ **ကပ်လျက် ဖြုတ်ချက်ကိုသာ** စစ်ရမည် — ဗီဒီယိုတစ်ခုလုံးရဲ့
        #    ဖြုတ်ချက်အားလုံးကို ဒီတောင်းချက်ရဲ့ အပြစ် မတင်ရ。
        # ⚠️ ဒီ ဖျက်ချက်နဲ့ **ကပ်လျက်** ဖြုတ်ချက်ကိုသာ ကြည့်ပြီး
        #    ခွင့်ပြုထားသော အပိုင်းအားလုံးကို ဖယ်သည်。
        outside = 0.0
        for x, y in gone:
            x, y = float(x), float(y)
            if y <= _lo or x >= _hi:
                continue                  # ဒီ ဖျက်ချက်နဲ့ မဆိုင်
            outside += _outside_sp(max(x, _lo - 1.0), min(y, _hi + 1.0))
        out.append((round(kept, 3), round(outside, 3)))
    return out
