#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ပြန်စ (retake) detector ကို လူ့ဖြတ်ချက် ground truth နဲ့ တိုင်းသည်。

⚠️ **တိုင်းရုံသာ** — ဗီဒီယို မဖြတ် · pipeline မထိ။ review စာရင်း ထုတ်သည်。
⚠️ Gemini တုံ့ပြန်ချက်ကို `--cache` မှာ သိမ်း — pick_guard ဖွင့်/ပိတ် နှိုင်းရာ ထပ်မခေါ်。
⚠️ precision/recall ကို **စကားပြော စက္ကန့်**နဲ့ တိုင်း (တိတ်ဆိတ်မှု မပါ) — ဇယား B ၁၅၀.၁s နဲ့ တူညီ。

  python3 tools/retake_eval.py --segs S.json --sp SP.json --sil SIL.json \\
      --gt assets/calib/c0736_retake_gt.json --cache C.json --out REVIEW.md
"""
import argparse, copy, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))
import clean as CL, cut as CUT

ap = argparse.ArgumentParser()
for k in ("segs", "sp", "sil", "gt", "cache", "out"): ap.add_argument("--" + k, required=True)
ap.add_argument("--brand", default="zjl")
A = ap.parse_args()
segs = json.load(open(A.segs)); sp = [tuple(x) for x in json.load(open(A.sp))]
sil = [tuple(x) for x in json.load(open(A.sil))]; gt = json.load(open(A.gt))
cal = CUT.calib(A.brand)
cache = json.load(open(A.cache)) if os.path.exists(A.cache) else {}

def ask(s, j, lo, hi):
    key = hashlib.sha1(json.dumps([j, lo, hi, [x["text"] for x in s[lo:hi]], CL.RETAKE_PROMPT],
                                  ensure_ascii=False).encode()).hexdigest()
    # ⚠️ **None ကို cache မသိမ်းရ** — သိမ်းလျှင် "ပြန်စ မဟုတ်" ဟု မှားယူပြီး
    #    နောက်တစ်ကြိမ် ထပ်မမေးတော့ (၂၀၂၆-၀၉-၁၆ ၆ ခု ဖြစ်ခဲ့)。
    if cache.get(key) is None:
        r = CL._ask_retake(s, j, lo, hi, __import__("asr").MODEL)
        if r is None: return None
        cache[key] = r
        json.dump(cache, open(A.cache, "w"), ensure_ascii=False)
    return cache[key]

def speech(iv):
    return sum(max(0, min(e, iv[1]) - max(s, iv[0])) for s, e in sp)
def speech_in(iv, parts):
    return sum(speech((max(iv[0], a), min(iv[1], b))) for a, b in parts if min(iv[1], b) > max(iv[0], a))

Bparts = [tuple(x) for u in gt["B"] for x in u["intervals"]]
Hparts = [tuple(x) for x in gt["human_removed"]]
Bsec = sum(speech(p) for p in Bparts)
meas = (sp, sil, gt["source_s"], None, "aroll")

def run(guard):
    c = copy.deepcopy(cal); c["retake"]["pick_guard"] = guard
    cuts, refused, st = CL.retakes(segs, meas, c, log=lambda *a: None, ask=ask)
    det = sum(speech((x["at"], x["to"])) for x in cuts)
    tpB = sum(speech_in((x["at"], x["to"]), Bparts) for x in cuts)
    tpH = sum(speech_in((x["at"], x["to"]), Hparts) for x in cuts)
    f2 = sum(1 for x in cuts for t in (x["at"], x["to"])
             if any(s < t < e for s, e in sp))
    top = {}
    for u in gt["B"]:
        if u["span"] in gt["top5"]:
            us = sum(speech(tuple(p)) for p in u["intervals"])
            got = sum(speech_in((x["at"], x["to"]), [tuple(p) for p in u["intervals"]]) for x in cuts)
            top[u["span"]] = (got / us) if us else 0.0
    return dict(cuts=cuts, refused=refused, st=st, det=det, tpB=tpB, tpH=tpH, f2=f2, top=top)

res = {g: run(g) for g in (True, False)}
print(f"ground truth B {len(gt['B'])} unit · စကား {Bsec:.1f}s\n")
for g, r in res.items():
    pB = r["tpB"] / r["det"] if r["det"] else float("nan")
    pH = r["tpH"] / r["det"] if r["det"] else float("nan")
    rc = r["tpB"] / Bsec if Bsec else 0
    t5 = sum(1 for v in r["top"].values() if v > 0.5)
    print(f"── pick_guard={'ဖွင့်' if g else 'ပိတ်'} · Gemini {r['st']['asked']} ကြိမ် · ဖျက် {len(r['cuts'])} · ငြင်း {len(r['refused'])} ──")
    print(f"  precision (B)          {pB:6.1%}   [≥95%] {'✓' if pB >= .95 else '✗'}")
    print(f"  precision (လူဖျက်တာ)  {pH:6.1%}   (ထားရမည့် စကားကို ဖျက် {r['det']-r['tpH']:.1f}s)")
    print(f"  recall (B)             {rc:6.1%}   [≥60%] {'✓' if rc >= .60 else '✗'}  ({r['tpB']:.1f}/{Bsec:.1f}s)")
    print(f"  F2 ဖြတ်မှတ် စကားပေါ်   {r['f2']}        [=0]  {'✓' if r['f2'] == 0 else '✗'}")
    print(f"  အကြီးဆုံး ၅ (>50%)     {t5}/5      [≥4]  {'✓' if t5 >= 4 else '✗'}  " +
          " · ".join(f"{k} {v:.0%}" for k, v in r["top"].items()))
    print(f"  stats {r['st']}\n")

r = res[True]
L = ["# C0736 · ပြန်စ (retake) review စာရင်း — pick_guard ဖွင့်", "",
     "⚠️ review စာရင်းသာ — ဗီဒီယို မဖြတ်ရသေး", "", "## ဖျက်မည်", "",
     "| အချိန် s | ကြာ | ဖျက်မည့် ဝါကျ | ချန်မည့် (နောက်ဆုံး take) | conf | B ကိုက် | လူဖျက်ထား |", "|---|---|---|---|---|---|---|"]
for x in r["cuts"]:
    iv = (x["at"], x["to"]); d = speech(iv)
    fb = speech_in(iv, Bparts) / d if d else 0; fh = speech_in(iv, Hparts) / d if d else 0
    units = [u["span"] for u in gt["B"] if speech_in(iv, [tuple(p) for p in u["intervals"]]) > 0]
    L.append(f"| {x['at']:.1f}–{x['to']:.1f} | {x['removed']:.1f} | #{x['sentences']} {x['text'][:90]} | "
             f"#{x['finals']} {x['keep'][:60]} | {x['conf']} | {fb:.0%} {','.join(units) or '—'} | {fh:.0%} |")
L += ["", "## ငြင်းခဲ့ (ဖြတ်မှတ် လုံခြုံမှု)", ""]
for x in r["refused"]:
    L.append(f"- #{x['sentences']} → #{x['finals']} · {x['reason']} · «{x['text'][:80]}»")
L += ["", "## လွတ်သွားသော B unit", ""]
for u in gt["B"]:
    us = sum(speech(tuple(p)) for p in u["intervals"])
    got = sum(speech_in((x["at"], x["to"]), [tuple(p) for p in u["intervals"]]) for x in r["cuts"])
    if us and got / us < 0.5:
        L.append(f"- {u['span']} · {u['intervals'][0][0]:.1f}s · စကား {us:.1f}s · ဖမ်းမိ {got/us:.0%}")
open(os.path.expanduser(A.out), "w").write("\n".join(L))
print("review ✓", A.out)
