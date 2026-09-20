#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · ချောင်းဆိုးသံ · ပြန်စ · ထပ်နေတဲ့စကား。

⚠️ ခွဲခြားချက် — အလိုအလျောက် ဖြတ်ခွင့်ရှိတာနဲ့ **ညွှန်ပြရုံသာ**:

  ✅ အလိုအလျောက်  ချောင်းဆိုးသံ · ဖြည့်စကား  (တိုင်းလို့ရ · ၇/၇)
  ⚠️ ညွှန်ပြရုံ    ပြန်စ · ထပ်နေတာ           (ဘယ်ဟာ ပြည့်စုံလဲ စက် မဆုံးဖြတ်နိုင်)

Zin ရဲ့ spec: "ဖြတ်စာရင်း ပြပြီး သူ အတည်ပြုမှ ဖြတ်ရမယ်"。
"""
import difflib, math, os, re, subprocess, wave
import measure as M

# ══ ပြန်စ ဆုံးဖြတ်ချက် မှတ်တမ်း ═══════════════════════════════
# ⚠️ ၂၀၂၆-၀၉-၁၇ (Zin) — မှတ်တမ်း မရှိသဖြင့် tokutei.mp4 မှာ «Gemini ကို
#    မေးလို့ မရခဲ့တာလား · မေးပြီး "မဟုတ်ဘူး" ဖြေခဲ့တာလား» ခွဲလို့ မရဘဲ
#    ပြန်ခေါ်ရသည်。 ⇒ **AI ရဲ့ ဆုံးဖြတ်ချက်တိုင်း မှတ်တမ်း ရှိရမည်**。
#    ⚠️ `_ask_retake` က retry ၃ ခါ ပြီးလျှင် **None** ပြန်ပြီး ခေါ်သူက အဲဒါကို
#       "retake မဟုတ်ပါ" နဲ့ **အတူတူ** ဆက်ဆံသည် (JSON ပျက်လျှင်လည်း တူတူ)
#       ⇒ status ကို ဒီမှာ ခွဲမှတ်မှသာ ခွဲခြားနိုင်သည်。
import json as _jsonl, time as _clk
_LOGF = os.environ.get("IKKI_RETAKE_LOG") or os.path.expanduser("~/.ikki/retake_ask.jsonl")
CTX = {}          # worker/eval က job_id · video စသည် ထည့်ထားနိုင်သည်


def _alog(**kw):
    """ပြန်စ ဆုံးဖြတ်ချက် တစ်ခုကို JSONL မှာ ထည့် — ရေးမရလျှင်လည်း job မပျက်ရ。"""
    try:
        rec = dict(t=_clk.strftime("%Y-%m-%dT%H:%M:%S"), **CTX, **kw)
        d = os.path.dirname(_LOGF)
        if d: os.makedirs(d, exist_ok=True)
        with open(_LOGF, "a", encoding="utf-8") as f:
            f.write(_jsonl.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


FILLER = {"အဲ","အာ","အင်း","အမ်","အော်","ဟို"}
# ⚠️ အဲ့ဒါ · အဲ့ဒီ · အဲ့လို က တကယ့်စကား — **ဖြုတ်လျှင် အဓိပ္ပာယ် ပျက်သည်**
KEEP   = ("အဲ့ဒါ","အဲ့ဒီ","အဲ့လို","အဲဒါ","အဲဒီ","အဲဒီလို")

def coughs(wav, min_d=0.06, max_d=0.80, lift=25.0, bridge=0.08):
    """high-band ပေါက်ကွဲမှု — median ထက် +25 dB (တိုင်းပြီး ၇/၇)。

    ⚠️ ချောင်းဆိုးသံက တလှုပ်လှုပ် ဖြစ်သဖြင့် hot frame တွေကို ~၈၀ms ကြား
       ပေါင်းပေးမှ တစ်ခုလုံး မိသည်။ မပေါင်းလျှင် လွတ်သွားသည်。
    """
    hi = M.band(wav, hp=3500, lp=7800)
    lo = M.band(wav, hp=180,  lp=3400)
    if not hi or not lo: return []
    n = min(len(hi), len(lo))
    rat = [(hi[i][0], hi[i][1]-lo[i][1]) for i in range(n)]
    vals = sorted(v for _,v in rat if v > -120)
    med = vals[len(vals)//2] if vals else -60
    hot = [t for t,v in rat if v > med + lift]
    if not hot: return []
    out=[]; s=hot[0]; p=hot[0]
    for t in hot[1:]:
        if t - p > bridge:
            if min_d <= p-s <= max_d: out.append((s, p))
            s = t
        p = t
    if min_d <= p-s <= max_d: out.append((s, p))
    return [dict(at=round(a,3), to=round(b,3), removed=round(b-a,3),
                 kind="cough", auto=True) for a,b in out]

def fillers(segs):
    """ဖြည့်စကား — စာသားထဲက **တစ်လုံးတည်း** ဖြစ်မှ。"""
    out=[]
    for s in segs:
        t = s["text"].strip()
        if any(k in t for k in KEEP): continue
        toks = [x for x in re.split(r"\s+", t) if x]
        if len(toks) == 1 and toks[0] in FILLER:
            out.append(dict(at=s["start"], to=s["end"],
                            removed=round(s["end"]-s["start"],3),
                            text=t, kind="filler", auto=True))
    return out

def restarts(segs, ratio=0.82, near=5):
    """ပြန်စ — **ကပ်လျက်** ဖြစ်ရမည်。

    ⚠️ window ကျယ်လျှင် ဖျက်ဆီးသည် — ၉၀ လုံး window နဲ့ "ကျွန်တော်" ကို
       စာကြောင်း ခြားပြီး တွဲမိပြီး ၃၇% ဖျက်မိတော့မည်ခဲ့。
    ⚠️ **နောက်ဟာ ထား၊ ရှေ့ဟာ ဖျက်** — ပထမက မကျသဖြင့် ပြန်စတာ (Zin သင်ခဲ့)。
    """
    out=[]
    for i in range(len(segs)-1):
        a,b = segs[i], segs[i+1]
        if b["start"] - a["end"] > 2.0: continue
        wa = a["text"].split(); wb = b["text"].split()
        if not wa or not wb: continue
        r = difflib.SequenceMatcher(None, wa[:near], wb[:near]).ratio()
        if r >= ratio:
            out.append(dict(at=a["start"], to=a["end"],
                            removed=round(a["end"]-a["start"],3),
                            text=a["text"], keep=b["text"], score=round(r,2),
                            kind="restart", auto=False))   # ⚠️ ညွှန်ပြရုံ
    return out

def repeats(segs, window=12):
    """ထပ်နေတဲ့ စကားစု — စာသားနဲ့ **အကြမ်းရှာရုံ**。

    ⚠️ တကယ် ဖြတ်ဖို့ **အသံ ဆင်တူမှု** (findrepeat · ၀.၈၇+) လိုသည်。
       ASR ရဲ့ စာလုံးအချိန်က ±၀.၃–၀.၅s ကွာသဖြင့် ±၃၀ms လိုတာ မမီ —
       အဲဒါနဲ့ ဖြတ်လျှင် **ဘေးက စာလုံး ဖြတ်မိသည်** (တကယ် ဖြစ်ခဲ့)。
       ထို့အပြင် chunk အဆက်မှာ ASR က **မရှိတဲ့ ထပ်နေမှု လုပ်ကြံသည်** (၄ ခုမှာ ၃ ခု)。
    ⚠️ ရည်ရွယ်ချက်ရှိ ဆင်တူဖွဲ့စည်းပုံ မဖြတ်ရ
       ("အလုပ်ဗီဇာနဲ့… ကျောင်းသားဗီဇာနဲ့…")。
    """
    out=[]
    for s in segs:
        toks = s["text"].split()
        # ⚠️ n=1 **မဖြုတ်ရ** — "ပေးတယ်ဆိုရင် ပေးတယ်ဆိုရင်" လို စာလုံး
        #    ချက်ချင်း ထပ်တာက Zin ရဲ့ spec ရဲ့ ပုံစံ ② ပါ。 n=2 ကနေ စလျှင်
        #    အဲဒါ လွတ်သွားသည် (တကယ် လွတ်ခဲ့)。
        for n in (1,2,3,4,5):
            for i in range(len(toks)-n*2+1):
                a = toks[i:i+n]; b = toks[i+n:i+n*2]
                if a == b and len(" ".join(a)) >= 3:
                    out.append(dict(at=s["start"], to=s["end"],
                        removed=0.0, text=" ".join(a), kind="repeat",
                        auto=False, note="အသံ ဆင်တူမှု စစ်ရန်"))
                    break
    return out

def plan(wav, segs, do_cough=True, do_filler=True):
    """(auto_cuts, flags) — auto ကိုသာ ဖြတ်၊ flags ကို သင် အတည်ပြုမှ。"""
    auto=[]; flags=[]
    if do_cough:  auto += coughs(wav)
    if do_filler: auto += fillers(segs)
    flags += restarts(segs) + repeats(segs)
    auto.sort(key=lambda c: c["at"])
    return auto, flags


# ══ ပြန်စ (retake) — ဝါကျ အဆင့် ═════════════════════════════════════
# ⚠️ C0736 လူ့ဖြတ်ချက် ခွဲခြမ်းချက် (၂၀၂၆-၀၉-၁၆): ပြန်စ **၁၅၀.၁s (၁၆.၂%)** —
#    silence ပြီးရင် အကြီးဆုံး။ အများစုက ဝါကျ/အပိုဒ် **တစ်ခုလုံး** မအောင်လို့
#    ချက်ချင်း ပြန်ပြောတာ ⇒ စာလုံးအချိန် မလို · ဝါကျ နယ်နိမိတ်နဲ့ ဖြတ်နိုင်。
# ⚠️ **review စာရင်းသာ** — ဂိတ် (precision ≥၉၅%) မအောင်မချင်း pipeline မချိတ်ရ。
# ⚠️ R7 — Gemini ကို **စာသား မထုတ်ခိုင်း** · နံပါတ်နဲ့ confidence သာ。
import json as _json, time as _time, urllib.request as _ur, urllib.error as _ue

RETAKE_SCHEMA = {"type": "OBJECT", "properties": {
    "same_attempt":     {"type": "BOOLEAN"},
    "earlier_attempts": {"type": "ARRAY", "items": {"type": "INTEGER"}},
    "confidence":       {"type": "NUMBER"}},
    "required": ["same_attempt", "earlier_attempts", "confidence"]}

RETAKE_PROMPT = (
    "အောက်ပါက ဗီဒီယို ရိုက်နေစဉ် ပြောသူ တစ်ယောက်ရဲ့ စကားကို ဝါကျအလိုက် နံပါတ်တပ်ထားတာပါ။\n"
    "ပြောသူက တစ်ခါတစ်ရံ ဝါကျ သို့မဟုတ် အပိုဒ်ကို မအောင်လို့ ရပ်ပြီး **ပြန်ပြော**တတ်တယ်။\n"
    "[J] အမှတ်အသား ပါတဲ့ ဝါကျ ({j}) ကို 'နောက်ဆုံး ပြောချက်' ဟု ယူပါ — နောက်က ဝါကျ ၁–၂ ခုက ဆက်ပိုင်း ဖြစ်နိုင်သည်။\n"
    "မေးခွန်း — {j} ရှေ့က ဝါကျတွေထဲမှာ {j} (နဲ့ ဆက်ပိုင်း) ကို ပြောဖို့ ကြိုးစားခဲ့ပြီး မအောင်ခဲ့လို့ ပြန်ပြောထားတဲ့ ဝါကျ ရှိလား။\n"
    "- အကြောင်းအရာ တူပြီး ပြန်ပြောထားမှသာ ထည့်ပါ\n"
    "- အကြောင်းအရာ **ဆက်ပြောနေတာ** (မတူတဲ့ အကြောင်း) ကို **မထည့်ရ** — သေချာမှသာ\n"
    "- same_attempt = ရှိလျှင် true · earlier_attempts = ဝါကျ နံပါတ်များ · confidence = 0 မှ 1\n"
    "- စာသား မပြန်ရ — နံပါတ်နဲ့ confidence သာ\n")

def _grams(t, n):
    t = re.sub(r"[\s။၊]+", "", t or "")
    return {t[i:i + n] for i in range(len(t) - n + 1)}

def _ask_retake(segs, j, lo, hi, model, log=print):
    lines = [f"{k + 1}. {'[J] ' if k == j else ''}{segs[k]['text']}" for k in range(lo, hi)]
    body = {"contents": [{"parts": [{"text": RETAKE_PROMPT.format(j=j + 1) + "\n" + "\n".join(lines)}]}],
            "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json",
                                 "responseSchema": RETAKE_SCHEMA}}
    import gemguard as G
    for i in range(3):
        G.throttle()
        r = _ur.Request(G.endpoint(model), data=_json.dumps(body).encode(),
                        headers={"Content-Type": "application/json"}, method="POST")
        try:
            with _ur.urlopen(r, timeout=120) as f:
                d = _json.loads(f.read())
            txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
            # ⚠️ JSON ပျက်တာနဲ့ ကွန်ရက် ကျတာကို **ခွဲမှတ်ရမည်** — return တန်ဖိုး
            #    နှစ်ခုလုံး None ဖြစ်၍ နောက်ပိုင်း ခွဲလို့ မရတော့。
            try:
                x = _json.loads(txt)
            except Exception as pe:
                G.tally("retake", False, f"parse {pe}")
                G.log_fail("retake", i + 1, 3, None, f"parse_fail: {type(pe).__name__}: {pe}")
                _alog(ev="ask", j=j + 1, status="parse_fail", tries=i + 1,
                      err=f"{type(pe).__name__}: {pe}", raw=(txt or "")[:200])
                _time.sleep(5 * (i + 1)); continue
            G.tally("retake", True)
            _alog(ev="ask", j=j + 1, status="ok", tries=i + 1,
                  same_attempt=bool(x.get("same_attempt")),
                  confidence=x.get("confidence"),
                  earlier_attempts=x.get("earlier_attempts") or [])
            return x
        except _ue.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            if G.fatal(e.code, raw):
                G.log_fail("retake", i + 1, 3, e.code, raw, final=True)
                _alog(ev="ask", j=j + 1, status="fatal", tries=i + 1, code=e.code, err=raw[:200])
                raise RuntimeError(f"Gemini ရပ်သွားပြီ: {raw[:200]}")
            mm = re.search(r'"retryDelay"\s*:\s*"(\d+)s"', raw)
            G.tally("retake", False, f"HTTP {e.code}")
            G.log_fail("retake", i + 1, 3, e.code, raw)
            _alog(ev="ask", j=j + 1, status="http_error", tries=i + 1, code=e.code, err=raw[:200])
            _time.sleep(int(mm.group(1)) if mm else 6 * (i + 1))
        except Exception as e:
            G.tally("retake", False, str(e)[:80])
            G.log_fail("retake", i + 1, 3, None, f"{type(e).__name__}: {e}")
            _alog(ev="ask", j=j + 1, status="error", tries=i + 1, err=f"{type(e).__name__}: {e}")
            _time.sleep(5 * (i + 1))
    G.log_fail("retake", 3, 3, None, "retry ကုန် — None ပြန်", final=True)
    _alog(ev="ask", j=j + 1, status="none", tries=3,
          note="retry ကုန် — None ပြန် (ခေါ်သူက 'retake မဟုတ်' နဲ့ အတူတူ ဆက်ဆံသည်)")
    return None

def retakes(segs, meas, cal, log=print, ask=None):
    """(cuts, refused, stats) — ပြန်စ ဝါကျများ · **နောက်ဆုံး take ချန် · ရှေ့အားလုံး ဖျက်**。

    `cal` = ချန်နယ် calib (`retake` block)。
    ⚠️ window ကို **ဝါကျ အရေအတွက်**နဲ့ ကန့်သတ် — စက္ကန့်နဲ့ မဟုတ် (R24 ၇၀s ကျော်)。
    ⚠️ ဖျက်မှု နယ်နိမိတ် — **စကား ဆုံး/onset ± edge** (တိတ်ဆိတ်မှု မလို · F2 စစ်)。
    ⚠️ Gemini ရွေးတာကို မျက်စိမှိတ် မယုံ — confidence · စာလုံးတူမှု (pick_guard) ·
       ထားမည့် ဝါကျ ထပ်မထိ · F2 စစ်ပြီးမှ လက်ခံ。
    """
    rc = cal["retake"]
    W, FS = int(rc["window_sentences"]), int(rc["final_span_sentences"])
    ov, gram = float(rc["candidate_overlap"]), int(rc["gram"])
    conf_min, guard = float(rc["min_confidence"]), bool(rc["pick_guard"])
    sp, sil = meas[0], meas[1]
    import asr as _A
    ask = ask or (lambda s, j, lo, hi: _ask_retake(s, j, lo, hi, _A.MODEL, log))
    n = len(segs)
    GR = [_grams(s["text"], gram) for s in segs]
    cover = lambda i, tgt: (len(GR[i] & tgt) / len(GR[i])) if GR[i] else 0.0
    deleted, st = {}, dict(candidates=0, asked=0, rejected_conf=0, guard_dropped=0)
    for j in range(n - 1, 0, -1):
        if j in deleted: continue
        lo, hi = max(0, j - W), min(n, j + FS)
        tgt = set().union(*GR[j:hi])
        cands = [i for i in range(lo, j) if i not in deleted and cover(i, tgt) >= ov]
        if not cands: continue
        st["candidates"] += 1
        _alog(ev="cand", fn="retakes", j=j + 1, lo=lo + 1, hi=hi,
              cands=[i + 1 for i in cands],
              cover={str(i + 1): round(cover(i, tgt), 3) for i in cands})
        res = ask(segs, j, lo, hi); st["asked"] += 1
        if not res or not res.get("same_attempt") or float(res.get("confidence", 0)) < conf_min:
            if res and res.get("same_attempt"): st["rejected_conf"] += 1
            _alog(ev="decide", fn="retakes", j=j + 1,
                  result=("no_answer" if not res else
                          ("not_same" if not res.get("same_attempt") else "low_conf")),
                  confidence=(res or {}).get("confidence"))
            continue
        picks = sorted({int(k) - 1 for k in res.get("earlier_attempts") or [] if lo <= int(k) - 1 < j})
        if guard:
            kept = [i for i in picks if cover(i, tgt) >= ov]
            st["guard_dropped"] += len(picks) - len(kept); picks = kept
        _alog(ev="decide", fn="retakes", j=j + 1, result="accept",
              confidence=res.get("confidence"), picks=[i + 1 for i in picks])
        for i in picks:
            if i not in deleted: deleted[i] = (j, float(res["confidence"]))
    # ── ဆက်တိုက် ဝါကျ အုပ်စု → **စကား နယ်နိမိတ်**ကို ကျောက်ချ ──
    # ⚠️ ၂၀၂၆-၀၉-၁၆ — "တိတ်ဆိတ်မှု ≥min_sil ထဲ စ·ဆုံး" ကို **ဖျက်ပြီး အစားထိုး**。
    #    တိုင်းချက်: run ၁၉ မှာ ၁၅ ခု "တိတ်ဆိတ်မှု မတွေ့" နဲ့ ငြင်း · recall
    #    ၆၇.၇% → ၂၀.၁%。 လူ့ဖြတ်မှတ် ၃၃% သာ တိတ်ဆိတ်မှုထဲ ကျ (calib) — retake
    #    က ချက်ချင်း ပြန်စ၍ ကြားမှာ ခဏရပ် မရှိ。 တိတ်ဆိတ်မှုက လုံခြုံမှုရဲ့
    #    **လက္ခဏာ** ဖြစ်ပေမဲ့ **လိုအပ်ချက် မဟုတ်**。
    #    ⇒ [ ရှေ့ချန်ဝါကျရဲ့ နောက်ဆုံး စကား (M.speech 20ms) + edge ,
    #        run နောက်က ပထမ ချန်ဝါကျရဲ့ onset − edge ]
    # ⚠️ "final take onset" မဟုတ်ဘဲ **နောက်က ပထမ ချန်ဝါကျ** — R24 လို ကြားမှာ
    #    ချန်ရမည့် ဝါကျ ရှိလျှင် final onset အထိ ဖျက်လျှင် အဲဒါတွေ ပါသွားမည်。
    # ⚠️ edge — `core/cut.py` `plan(edge=…)` ရဲ့ ပုံသေ (R5 · ဂဏန်း ထပ်မရေး)。
    runs, cur = [], []
    for i in sorted(deleted):
        if cur and i != cur[-1] + 1: runs.append(cur); cur = []
        cur.append(i)
    if cur: runs.append(cur)
    import inspect, cut as _CUT
    edge = float(inspect.signature(_CUT.plan).parameters["edge"].default)
    cuts, refused = [], []
    for run in runs:
        i1, i2 = run[0], run[-1]
        nk = i2 + 1 if i2 + 1 < n else None
        info = dict(sentences=[i + 1 for i in run], finals=sorted({deleted[i][0] + 1 for i in run}),
                    next_kept=(nk + 1 if nk is not None else None),
                    conf=round(min(deleted[i][1] for i in run), 2),
                    text=" ‖ ".join(segs[i]["text"] for i in run),
                    keep=" ‖ ".join(segs[f - 1]["text"] for f in sorted({deleted[i][0] + 1 for i in run})))
        # ⚠️ **နှစ်ဖက်စလုံး M.speech() နဲ့ ကျောက်ချ** (၂၀၂၆-၀၉-၁၆ Zin ခွင့်ပြု) —
        #    ① စဘက် `prev_end + edge` — ပြန်စ ကြား gap ၀.၀၂s သာ ဖြစ်၍ ဖျက်မည့်
        #       စကားထဲ ဝင်ခဲ့ (F2 ၄ ခု) ⇒ gap < 2×edge ဆိုလျှင် **gap အလယ်**
        #    ② ဆုံးဘက် ASR onset — စကားစထက် ၀.၁၈s နောက်ကျခဲ့ (F2 ၃ ခု) ⇒
        #       ချန်ဝါကျရဲ့ **M.speech စကားစ**၊ gap စည်းမျဉ်း တူတူ
        #    ဖြတ်မှတ် နှစ်ခုလုံး စကား ပြင်ပ — F2 စစ်ချက်က ဆုံးဖြတ်သည်。
        prev_end = max((e for s_, e in sp if e <= segs[i1]["start"]), default=None)
        del_on = (min((s_ for s_, e in sp if s_ >= prev_end), default=None)
                  if prev_end is not None else None)
        keep_on = del_end = None
        if nk is not None:
            on = segs[nk]["start"]
            inside = [s_ for s_, e in sp if s_ <= on < e]
            keep_on = inside[0] if inside else min((s_ for s_, e in sp if s_ >= on), default=None)
            if keep_on is not None:
                del_end = max((e for s_, e in sp if e <= keep_on), default=None)
        if None in (prev_end, del_on, keep_on, del_end):
            refused.append(dict(info, reason="ရှေ့/နောက် စကား နယ်နိမိတ် မရ")); continue
        pt = lambda end_, start_, side: ((end_ + start_) / 2.0 if start_ - end_ < 2 * edge
                                         else (end_ + edge if side == "a" else start_ - edge))
        a, b = pt(prev_end, del_on, "a"), pt(del_end, keep_on, "b")
        if b <= a:
            refused.append(dict(info, reason="နယ်နိမိတ် ပြောင်းပြန်")); continue
        # ချန်ဝါကျ **onset** တစ်ခုခု ဖျက်ကွက်ထဲ ကျလျှင် — အဲဒီဝါကျ ပါသွားမည်
        hit = [k + 1 for k in range(n) if k not in deleted and a < segs[k]["start"] < b]
        if hit:
            refused.append(dict(info, reason=f"ထားမည့် ဝါကျ {hit} ကို ထိ")); continue
        if M.in_speech(a, sp) or M.in_speech(b, sp):
            refused.append(dict(info, reason="F2 ဖြတ်မှတ် စကားပေါ် ကျ")); continue
        cuts.append(dict(info, at=round(a, 3), to=round(b, 3), removed=round(b - a, 3),
                         kind="retake", auto=False))
    st.update(runs=len(runs), cuts=len(cuts), refused=len(refused),
              removed=round(sum(c["removed"] for c in cuts), 2))
    return cuts, refused, st


# ══ review mode v2 — «စက်က အုပ်စု ရှာ · လူက take ရွေး» (၂၀၂၆-၀၉-၁၆ Zin) ══
# ⚠️ ဘယ် take ချန်မလဲ **စက်က မဆုံးဖြတ်ရ** — တိုင်းချက်: ချန်ထားသော take က ရှေ့မှာ
#    ဖြစ်တာ ၂၃/၆၇ = ၃၄% (podcast ၁၁/၂၁ = ၅၂%) ⇒ "နောက်ဆုံး take ချန်" စည်းမျဉ်းက
#    သုံးပုံတစ်ပုံ မှား。 ဤ function က **အုပ်စု + ရွေးစရာ** သာ ထုတ်သည် — မဖျက်ပါ。
def _drop_intervals(segs, sp, drop_idx, edge, dur=None):
    """([[a,b],…], None) | (None, အကြောင်းရင်း) — ဖျက်မည့် ဝါကျများ → လုံခြုံသော ဖြတ်မှတ်。

    နယ်နိမိတ်က `retakes()` နဲ့ **အတူတူ** (M.speech ကျောက်ချ · gap အလယ် · F2 စစ်)。

    ⚠️ **ဖိုင်အစ / ဖိုင်အဆုံး anchor** (၂၀၂၆-၀၉-၁၇ Zin ခွင့်ပြု) — ဖျက်ရမည့် အပိုင်းက
       ဗီဒီယိုရဲ့ **ပထမဆုံး စကား**ကနေ စလျှင် ရှေ့မှာ anchor မရှိသဖြင့် ယခင်က
       **ငြင်းပယ်**ခဲ့သည် ⇒ C0088 cl00 မှာ နိဒါန်း take ၅ ခုထဲ take 1 သာ ရွေးလို့ရဘဲ
       **နာမည် မှားနေသော take** ကျန်ခဲ့သည် (Zin ၂၀၂၆-၀၉-၁၇)。
       တိုင်းချက် — ဖိုင်အစကနေ ပထမ စကားအထိ ၃၃၆၀ms တိတ်ဆိတ် ⇒ `a = 0.0` မှာ ဖြတ်လျှင်
       စကား **၀ ms** ထိ。 ထို့အတူ နောက်ဆုံး ဝါကျအထိ ဖျက်လျှင် `b = dur`。
       `dur` မပေးလျှင် ယခင်အတိုင်း ငြင်းသည် (backward compatible)。
    """
    n, drop = len(segs), sorted(drop_idx)
    if not drop: return [], None
    runs, cur = [], []
    for i in drop:
        if cur and i != cur[-1] + 1: runs.append(cur); cur = []
        cur.append(i)
    if cur: runs.append(cur)
    out = []
    for run in runs:
        i1, i2 = run[0], run[-1]
        nk = i2 + 1 if i2 + 1 < n else None
        prev_end = max((e for s_, e in sp if e <= segs[i1]["start"]), default=None)
        del_on = (min((s_ for s_, e in sp if s_ >= prev_end), default=None)
                  if prev_end is not None else None)
        keep_on = del_end = None
        if nk is not None:
            on = segs[nk]["start"]
            inside = [s_ for s_, e in sp if s_ <= on < e]
            keep_on = inside[0] if inside else min((s_ for s_, e in sp if s_ >= on), default=None)
            if keep_on is not None:
                del_end = max((e for s_, e in sp if e <= keep_on), default=None)
        head = prev_end is None and del_on is None      # ဖိုင်အစကနေ ဖျက်မည်
        tail = nk is None and dur is not None            # ဖိုင်အဆုံးအထိ ဖျက်မည်
        # ⚠️ ငြင်းလျှင် **ဘယ်ဖျက်ချက်ကြောင့်လဲ အတိအကျ** ပြန်ပြောရမည် (Zin ၂၀၂၆-၀၉-၁၈) —
        #   "ဗီဒီယို လုံးဝ မထွက်" ဆိုသော တိတ်ဆိတ် ကျရှုံးမှုကို လက်မခံပါ。
        wh = f"ဝါကျ {[k + 1 for k in run]}"
        if (prev_end is None or del_on is None) and not head:
            return None, f"{wh} — ရှေ့ စကား နယ်နိမိတ် မရ"
        if (keep_on is None or del_end is None) and not tail:
            return None, f"{wh} — နောက် စကား နယ်နိမိတ် မရ"
        pt = lambda end_, start_, side: ((end_ + start_) / 2.0 if start_ - end_ < 2 * edge
                                         else (end_ + edge if side == "a" else start_ - edge))
        a = 0.0 if head else pt(prev_end, del_on, "a")
        b = float(dur) if tail else pt(del_end, keep_on, "b")
        if b <= a: return None, f"{wh} — နယ်နိမိတ် ပြောင်းပြန်"
        hit = [k + 1 for k in range(n) if k not in drop and a < segs[k]["start"] < b]
        if hit: return None, f"{wh} — ထားမည့် ဝါကျ {hit} ကို ထိ"
        if M.in_speech(a, sp) or M.in_speech(b, sp):
            return None, f"{wh} — F2 ဖြတ်မှတ် စကားပေါ် ကျ"
        out.append([round(a, 3), round(b, 3)])
    return out, None


def retake_clusters(segs, meas, cal, log=print, ask=None):
    """(clusters, stats) — အုပ်စု စာရင်း · **ဘာမှ မဖျက်**。

    cluster = {id, takes:[{n,i,start,end,text}], options:{"take နံပါတ်" → [[a,b],…]},
               blocked:{take → အကြောင်းရင်း}, conf, span}
    `options[t]` = take `t` ကို ချန်ပြီး ကျန်တာ ဖျက်လျှင် ဖြတ်မှတ်များ (F2 စစ်ပြီးသား)。
    """
    rc = cal["retake"]
    W, FS = int(rc["window_sentences"]), int(rc["final_span_sentences"])
    ov, gram = float(rc["candidate_overlap"]), int(rc["gram"])
    conf_min, guard = float(rc["min_confidence"]), bool(rc["pick_guard"])
    sp = meas[0]
    import asr as _A, inspect, cut as _CUT
    ask = ask or (lambda s, j, lo, hi: _ask_retake(s, j, lo, hi, _A.MODEL, log))
    edge = float(inspect.signature(_CUT.plan).parameters["edge"].default)
    n = len(segs)
    GR = [_grams(s["text"], gram) for s in segs]
    cover = lambda i, tgt: (len(GR[i] & tgt) / len(GR[i])) if GR[i] else 0.0
    st = dict(candidates=0, asked=0, rejected_conf=0, guard_dropped=0)
    groups, used = [], set()
    for j in range(n - 1, 0, -1):
        # ⚠️ `retakes()` ရဲ့ `if j in deleted: continue` နဲ့ ညီအောင် — အုပ်စုတစ်ခုမှာ
        #    ရှေ့ take အဖြစ် ပါပြီးသား ဝါကျကို ထပ်မမေး (Gemini ခေါ်ဆိုမှု ~၂၅% ပို)。
        if j in used: continue
        lo, hi = max(0, j - W), min(n, j + FS)
        tgt = set().union(*GR[j:hi])
        _cd = [i for i in range(lo, j) if cover(i, tgt) >= ov]
        if not _cd: continue
        st["candidates"] += 1
        _alog(ev="cand", fn="clusters", j=j + 1, lo=lo + 1, hi=hi,
              cands=[i + 1 for i in _cd],
              cover={str(i + 1): round(cover(i, tgt), 3) for i in _cd})
        res = ask(segs, j, lo, hi); st["asked"] += 1
        if not res or not res.get("same_attempt") or float(res.get("confidence", 0)) < conf_min:
            if res and res.get("same_attempt"): st["rejected_conf"] += 1
            _alog(ev="decide", fn="clusters", j=j + 1,
                  result=("no_answer" if not res else
                          ("not_same" if not res.get("same_attempt") else "low_conf")),
                  confidence=(res or {}).get("confidence"))
            continue
        picks = sorted({int(k) - 1 for k in res.get("earlier_attempts") or [] if lo <= int(k) - 1 < j})
        if guard:
            kept = [i for i in picks if cover(i, tgt) >= ov]
            st["guard_dropped"] += len(picks) - len(kept); picks = kept
        if picks:
            groups.append((set(picks + [j]), float(res["confidence"]))); used.update(picks)
        _alog(ev="decide", fn="clusters", j=j + 1,
              result=("accept" if picks else "guard_empty"),
              confidence=res.get("confidence"), picks=[i + 1 for i in picks])
    # ── အုပ်စု ပေါင်း — ① ဝါကျ မျှသုံး ② အချိန် ထပ် (UI မှာ တစ်ခုတည်း ပြရန်) ──
    def merge(items, linked):
        par = list(range(len(items)))
        def find(x):
            while par[x] != x: par[x] = par[par[x]]; x = par[x]
            return x
        for i in range(len(items)):
            for k in range(i + 1, len(items)):
                if linked(items[i][0], items[k][0]): par[find(i)] = find(k)
        out = {}
        for i, (g, c) in enumerate(items):
            r = find(i); cur = out.setdefault(r, [set(), c])
            cur[0].update(g); cur[1] = min(cur[1], c)
        return [(g, c) for g, c in out.values()]
    hull = lambda s: (segs[min(s)]["start"], segs[max(s)]["end"])
    items = merge(groups, lambda a, b: bool(a & b))
    items = merge(items, lambda a, b: min(hull(a)[1], hull(b)[1]) > max(hull(a)[0], hull(b)[0]))
    clusters = []
    for k, (idxs, conf) in enumerate(sorted(items, key=lambda v: min(v[0]))):
        idx = sorted(idxs)
        takes = [dict(n=t + 1, i=i + 1, start=round(segs[i]["start"], 2),
                      end=round(segs[i]["end"], 2), text=segs[i]["text"])
                 for t, i in enumerate(idx)]
        opts, blocked = {}, {}
        for t, keep_i in enumerate(idx):
            iv, why = _drop_intervals(segs, sp, [i for i in idx if i != keep_i], edge,
                                      dur=meas[2])
            if iv is None: blocked[str(t + 1)] = why
            else: opts[str(t + 1)] = iv
        clusters.append(dict(id=f"cl{k:02d}", takes=takes, options=opts, blocked=blocked,
                             conf=round(conf, 2),
                             span=[round(segs[idx[0]]["start"], 2), round(segs[idx[-1]]["end"], 2)]))
    st.update(clusters=len(clusters), takes=sum(len(c["takes"]) for c in clusters),
              blocked=sum(len(c["blocked"]) for c in clusters))
    return clusters, st
