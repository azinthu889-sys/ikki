#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""template တစ်ခုချင်း၏ **မှင် ဒေါင်လိုက် နေရာ** ကို တိုင်းသည်

    python3 tools/gfxypos.py [--fmt=9:16] [--only id,id] [--write]

⚠️⚠️ **ဒါက `gfxsize.py` ရဲ့ အမြင့်ကို အစားထိုးတာ မဟုတ်** — အမြင့်ကိုသာ
   သိလျှင် 「ဘယ်မှာ ချရမလဲ」 မသိ。 `dress.track()` က render ချိန်မှာ
   `_ybox()` နဲ့ တကယ့် element ကို တိုင်းသည် ⇒ **ချချိန် တိုင်းချက် မလို**。
   ဒီဖိုင်က **ရွေးချိန်** အတွက် — `fits()` မှာ 「ဘောင်အပြည့် မြင့်」 ဆိုပြီး
   ပယ်ခံရသူ တကယ် ဝင်မဝင် ဆုံးဖြတ်ရန်。

⚠️ **ပြဿနာ: `alpha > 8` က မှိန်သော နောက်ခံလွှာကိုပါ 「မှင်」 ဟု မှတ်သည်**。
   `gfx_size_9x16.json` မှာ template ၉၆/၆၁၇ က `h_pct ≥ 0.90` ထွက်သည်
   (thm ၁၅ · retro ၁၀ · prem* ၆၃ …)。 `insert.insert_label` က ၀.၉၉၉၅ —
   တကယ့် label က သေးလျက် ဘောင်အပြည့် veil ဆွဲထားလျှင် `fits()` က
   ၉:၁၆ မှာ **အခွင့်မရှိဘဲ ပယ်**မည် (ပြောသူ ၀–၆၂% · စာတန်း ၇၀% ⇒
   ကျန် ၁၅၄px သာ)。
   ⇒ threshold ၄ မျိုးနဲ့ အတူ တိုင်းပြီး **ဖြန့်ကျက်မှု** ပြသည်။
   ဂိတ် ကိန်းကို ဖြန့်ကျက်မှု မကြည့်ခင် မသတ်မှတ်ရ ([[measure-distribution-rule]])。

⚠️ `--write` မပါလျှင် ဖိုင် မရေး — တိုင်းချက်သာ ပြသည်。
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "core"))
TIMEOUT = 90

CHILD = r'''
import os, sys, json
sys.path.insert(0, os.path.join(%(HERE)r, "core"))
import gfxcat as G, dress as DR, formats as FM
if G.MK not in sys.path: sys.path.insert(0, G.MK)
import theme as TH
import numpy as np
from PIL import Image
eid = sys.argv[1]
fmt = sys.argv[2] if len(sys.argv) > 2 else "16:9"
# production bhoin — `gfxsize.py` နဲ့ အတိအကျ တူရမည်
_bd = dict(id="ikki", colors=None, mmf=None, latin=None, jp=None)
try:
    _base = dict(TH.THEMES.get("ikki") or TH.THEMES[list(TH.THEMES)[0]])
    _bd = dict(id="ikki",
               colors=[_base["NAVY"], _base["DEEP"], _base["GOLD"],
                       _base["SKY"], _base["RED"]],
               mmf=_base["MMF"], latin=_base["LATIN"], jp=_base["JP"])
    TH.THEMES["_ikki"] = FM.theme(_bd, fmt)
    TH.use("_ikki")
except Exception as _e:
    print(json.dumps({"ok":0,"why":"theme %%s" %% _e})); raise SystemExit
e = [x for x in G.catalog() if x["id"] == eid]
if not e: print(json.dumps({"ok":0,"why":"id မတွေ့"})); raise SystemExit
e = e[0]
args = G.fill(e, "ဂျပန်မှာ အလုပ်", "ZAE", 62)
if not args: print(json.dumps({"ok":0,"why":"fill ဗလာ"})); raise SystemExit
# ⚠⚠ **tag ကို ကိုယ်ပိုင် ရေးရမည်** — `"g0"` က `dress` ရဲ့ tag နဲ့ ထပ်ပြီး
# ရှင်းချက် ရှင်းပြီး render နဲ့ အပြိုင် ပြေးလျှင် frame အချင်း ဖျက်မိမည်。
import hashlib as _hh
TAG = "yp" + _hh.sha1(eid.encode()).hexdigest()[:8]
if DR._wants_tag(e["fn"]): args = (TAG,) + tuple(args)
el = G.call(e, args, 2.0)
if not isinstance(el, dict):
    print(json.dumps({"ok":0,"why":"dict မဟုတ်"})); raise SystemExit
def rp(q): return q if os.path.isabs(q) else os.path.join(G.MK, q)
anim = list(el.get("anim") or [])
if len(anim) < 2:
    print(json.dumps({"ok":0,"why":"ဖရိမ်း %%d" %% len(anim)})); raise SystemExit
seq = list(anim[len(anim)//2:]) + [(q,x,y) for q,x,y,_d in el.get("statics",[])]
_d = TH.t(); H, W = int(_d["H"]), int(_d["W"])
# ⚠️ **ဘောင်အပြည့်ပေါ် ချပြီးမှ** တိုင်းရမည် — strip PNG က offset ရှိသည်
#    (`gfx_cutaway.py` ရဲ့ သင်ခန်းစာ) ⇒ row-mass က ဘောင်နဲ့ တန်းရမည်。
rows = np.zeros(H, dtype="float64")      # alpha mass per row (အများဆုံး ဖရိမ်း)
best = -1.0
box = {}
for it in seq:
    q = rp(it[0] if isinstance(it,(list,tuple)) else it)
    if not os.path.exists(q): continue
    im = Image.open(q).convert("RGBA")
    a = np.asarray(im)[:,:,3].astype("float32") / 255.0
    oy = it[2] if isinstance(it,(list,tuple)) and len(it) > 2 else 0
    ox = it[1] if isinstance(it,(list,tuple)) and len(it) > 1 else 0
    cv = np.zeros((H, W), dtype="float32")
    y1c = min(H, oy + a.shape[0]); x1c = min(W, ox + a.shape[1])
    if y1c <= oy or x1c <= ox: continue
    cv[oy:y1c, ox:x1c] = a[:y1c-oy, :x1c-ox]
    m = float(cv.sum())
    if m > best:
        best = m
        rows = cv.sum(axis=1).astype("float64")
        # threshold အမျိုးမျိုးနဲ့ bbox
        for nm, th in (("t8", 8/255.0), ("t64", 64/255.0),
                       ("t128", 128/255.0), ("t200", 200/255.0)):
            ys = np.nonzero(cv.max(axis=1) > th)[0]
            box[nm] = ([int(ys.min()), int(ys.max())] if len(ys) else None)
if best <= 0:
    print(json.dumps({"ok":0,"why":"မှင် မရှိ"})); raise SystemExit
tot = rows.sum()
cum = np.cumsum(rows) / max(1e-9, tot)
def qy(p):
    i = int(np.searchsorted(cum, p))
    return int(min(H-1, max(0, i)))
cy = float((rows * np.arange(H)).sum() / max(1e-9, tot))
out = {"ok":1, "H":H, "W":W,
       "cy": round(cy / H, 4),              # alpha-အလေးချိန် အလယ်မှတ်
       "m02": qy(0.02), "m50": qy(0.50), "m98": qy(0.98),
       "mass": round(float(tot) / (H*W), 5)}
for nm in ("t8","t64","t128","t200"):
    b = box.get(nm)
    out[nm] = b
    out[nm+"_h"] = (None if not b else round((b[1]-b[0]) / float(H), 4))
out["mh"] = round((out["m98"] - out["m02"]) / float(H), 4)
print(json.dumps(out))
''' % {"HERE": HERE}


def main(argv):
    import gfxcat as G
    fmt = "16:9"
    for a in argv[1:]:
        if a.startswith("--fmt="):
            fmt = a.split("=", 1)[1]
    js = os.path.join(HERE, "assets",
                      "gfx_ypos_%s.json" % fmt.replace(":", "x"))
    ids = [e["id"] for e in G.catalog()]
    if "--only" in argv:
        want = set(argv[argv.index("--only") + 1].split(","))
        ids = [i for i in ids if i in want]
    # ⚠️ **တစ်ခုပြီးတိုင်း သိမ်းရမည်** — ရပ်သွားလည် တိုင်းချက် မပျောက်ရ
    #    (`gfx_cutaway.py` မှာ ၂၁/၃၉ အလဟဿ ဖြစ်ခဲ့သော သင်ခန်းစာ)。
    try:
        cache = json.load(open(js, encoding="utf-8")).get("items") or {}
    except (OSError, ValueError, AttributeError):
        cache = {}
    force = "--force" in argv
    todo = [i for i in ids if force or i not in cache]
    print("── %s · တိုင်းမည် %d/%d (cache %d) ──"
          % (fmt, len(todo), len(ids), len(cache)), flush=True)
    t0 = time.time()
    for k, eid in enumerate(todo, 1):
        try:
            r = subprocess.run([sys.executable, "-c", CHILD, eid, fmt],
                               capture_output=True, text=True, timeout=TIMEOUT)
            ln = [x for x in (r.stdout or "").strip().splitlines() if x.strip()]
            d = json.loads(ln[-1]) if ln else {}
            if not d.get("ok") and not d.get("why"):
                _er = [x for x in (r.stderr or "").strip().splitlines()
                       if x.strip()]
                d["why"] = (_er[-1][:120] if _er
                            else "stdout ဗလာ · rc=%s" % r.returncode)
        except (subprocess.TimeoutExpired, ValueError, IndexError) as e:
            d = {"ok": 0, "why": type(e).__name__}
        cache[eid] = d
        # ⚠️ ယာယီ frame ရှင်း — မရှင်းလျှင် `motionkit/work` က GB ချီ တက်သည်
        try:
            import glob as _g
            for _dd in _g.glob(os.path.join(G.MK, "work", "*")):
                for _f in _g.glob(os.path.join(_dd, "*yp*")):
                    try:
                        os.remove(_f)
                    except OSError:
                        pass
        except Exception:
            pass
        json.dump({"version": 1, "fmt": fmt, "n": len(ids),
                   "_doc": "tools/gfxypos.py — မှင် ဒေါင်လိုက် နေရာ "
                           "(alpha mass · threshold ၄ မျိုး)",
                   "items": cache},
                  open(js, "w"), ensure_ascii=False, indent=1)
        if d.get("ok"):
            print("  [%3d/%3d] %-30s cy %.3f · mass-h %.3f · t8-h %.3f"
                  % (k, len(todo), eid, d["cy"], d["mh"], d.get("t8_h") or 0),
                  flush=True)
        else:
            print("  [%3d/%3d] %-30s ✖ %s"
                  % (k, len(todo), eid, str(d.get("why"))[:46]), flush=True)
    print("\n── ပြီး %.0fs ──" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
