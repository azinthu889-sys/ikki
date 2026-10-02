#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""template ရဲ့ **စာသား ဖတ်နိုင်မှု** (ကွာခြားချက်) ကို တိုင်းသည်

    python3 tools/gfxcontrast.py [--fmt=9:16] [--only id,id]

⚠️ **ဤအရာကို တိုင်းသော ဂိတ် မရှိခဲ့ပါ**。 `tools/gfxqual.py` က gradient
   သိပ်သည်းမှု + Vision အနား အကွာအဝေးကိုသာ တိုင်းသည် ⇒ အမှောင် box ပေါ်
   အမှောင် စာ ဆိုလျှင် အောင်သွားမည် (WCAG: စာကြီး ≥ ၃.၀ · ပုံမှန် ≥ ၄.၅)。

⚠️⚠️ **alpha နဲ့ စာသားကို ကတ်အခွံကနေ မခွဲနိုင်ပါ** — ကတ်မှာ နှစ်ခုလုံး
   alpha ၁.၀ ဖြစ်သည် ⇒ alpha နဲ့ ခွဲလျှင် 「မှင်」က ကတ်တစ်ခုလုံး ဖြစ်ပြီး
   အနားပတ်လည်က ဗီဒီယိုနေရာ (ပွင့်လင်း) ဖြစ်သွားကာ **ကတ် vs နောက်ခံ** ကို
   တိုင်းမိမည်、စာ vs ကတ် မဟုတ်。 ⇒ **အလင်းပိတ် အပြည့် ကွက် (၃၂×၃၂)**
   အတွင်းက အလင်း ဖွဲ့စည်းပုံ (p90 vs p10) ကို တိုင်းပြီး ကွက်များရဲ့
   **အလယ်မှတ်** ယူသည် (အဆိုးဆုံး = noise · အကောင်းဆုံး = ဝါရောင် ဂဏန်း
   တစ်ခုက ကတ်တစ်ခုလုံးကို အောင်စေမည်)。

⚠️ **IKKI ရဲ့ တကယ့်လမ်းကြောင်းနဲ့ တိုင်းရမည်** — `demoargs` က template ရဲ့
   ကိုယ်ပိုင် နမူနာ ဖြစ်ပြီး အရောင် မတူပါ。 `dress` က `_tf_args` နဲ့
   accent/ink/dim ပို့သည် ⇒ အဲဒါကို အရင် ကြိုးသည်、မရမှ demoargs。

⚠️⚠️ ဤဂိတ်က ၂၀၂၆-၁၀-၀၂ မှာ **ငါ့ကို ပြန်တည့်မတ်ပေး**ခဲ့သည် —
   render ဖရိမ်းကနေ `qcard.num_point` ကို 「၁.၇၅:၁ ⇒ မဖတ်နိုင်」 ဟု
   တိုင်းခဲ့ပြီး ဂိတ်က ၁၈.၉:၁ ပြသည်。 **ဂိတ်က မှန်သည်** — ငါ ကတ်
   ဝင်လာစ (+၀.၆s) ဖရိမ်းကို ယူမိခြင်း ဖြစ်ပြီး ၂၅.၅s မှာ ၁၆.၇:၁ ရသည်
   ([[ikki-settled-frame-rule]])。 ကိရိယာနဲ့ လက်တိုင်းချက် ကွဲလျှင်
   **လက်တိုင်းချက်ကို အရင် သံသယဝင်ရမည်**。
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "core"))
TIMEOUT = 90
MIN_RATIO = 3.0                      # ⚠️ ဖြန့်ကျက်မှု ကြည့်ပြီးမှ တင်းရန်

CHILD = r'''
import os, sys, json
sys.path.insert(0, os.path.join(%(HERE)r, "core"))
import gfxcat as G, dress as DR, formats as FM
if G.MK not in sys.path: sys.path.insert(0, G.MK)
import theme as TH
import numpy as np
from PIL import Image
eid = sys.argv[1]; fmt = sys.argv[2] if len(sys.argv) > 2 else "16:9"
# ⚠️⚠️ **ဆောက်ခြင်းရဲ့ ရှေ့မှာ motionkit ဖိုလ်ဒါသို့ ပြောင်းရမည်**。
#    `infogfx.OUT` က `work/<sub>` (ဆွေမျိုး လမ်းကြောင်း) ဖြစ်ပြီး `rp()` က
#    `G.MK` ကို ရှေ့တိုးသည် ⇒ chdir မလုပ်လျှင် PNG တွေက `~/ikki/work` ထဲ
#    ရောက်ပြီး `os.path.exists` က အမြဲ False ⇒ ဖရိမ်း တစ်ခုမှ မတိုင်းဖြစ်ဘဲ
#    「မှင် မလုံလောက်」 ထွက်သည် (၂၀၂၆-၁၀-၀၂ ဖမ်းမိ)。
os.chdir(G.MK)
try:
    _b = dict(TH.THEMES.get("ikki") or TH.THEMES[list(TH.THEMES)[0]])
    TH.THEMES["_c"] = FM.theme(dict(id="ikki",
        colors=[_b["NAVY"], _b["DEEP"], _b["GOLD"], _b["SKY"], _b["RED"]],
        mmf=_b["MMF"], latin=_b["LATIN"], jp=_b["JP"]), fmt)
    TH.use("_c")
except Exception as _e:
    print(json.dumps({"ok":0,"why":"theme %%s" %% _e})); raise SystemExit
e = [x for x in G.catalog() if x["id"] == eid]
if not e: print(json.dumps({"ok":0,"why":"id မတွေ့"})); raise SystemExit
e = e[0]
import hashlib as _hh
TAG = "ct" + _hh.sha1(eid.encode()).hexdigest()[:8]
# ⚠️⚠️ **IKKI ရဲ့ တကယ့်လမ်းကြောင်းကို အရင် ကြိုးရမည်**。
#    `demoargs` က template ရဲ့ ကိုယ်ပိုင် နမူနာ ဖြစ်ပြီး **အရောင် မတူ**ပါ —
#    `qcard.num_point` က demoargs နဲ့ ၁၅.၈၄:၁ ထွက်ပြီး တကယ့် render မှာ
#    **၁.၇၅:၁** ဖြစ်ခဲ့သည် (၁၀၇ အဆင့် ကွာ)。 `dress` က `_tf_args` နဲ့
#    accent/ink/dim ပို့သည် ⇒ အဲဒီလမ်းကြောင်းကိုသာ တိုင်းရမည်。
args = None
kw = None
try:
    kw = DR._tf_args(dict(kind=eid, text="ဂျပန်မှာ အလုပ်ရှာဖွေခြင်း",
                          items=["ဂျပန်", "ပညာသင်", "ဗီဇာ"], num="62"),
                     accent=(TH.t() or {}).get("GOLD") or "#FFE000",
                     ink=(TH.t() or {}).get("INK") or "#FFFFFF",
                     dim=(TH.t() or {}).get("DIM") or "#8B8B8B")
except Exception:
    kw = None
if not kw:
    try:
        import demoargs as _DA
        _t = TH.t()
        args = _DA.resolve(e["module"], e["fn"], int(_t["W"]), int(_t["H"]))
    except BaseException:
        args = None
    if not args:
        args = G.fill(e, "ဂျပန်မှာ အလုပ်", "ZAE", 62)
    if not args:
        print(json.dumps({"ok":0,"why":"fill ဗလာ"})); raise SystemExit
try:
    if kw is not None:
        _m = __import__(e["module"])
        _fn = getattr(_m, "BUILDERS", {}).get(e["fn"]) or getattr(_m, e["fn"])
        el = DR._call_template(_fn, eid, TAG, kw)
    else:
        if DR._wants_tag(e["fn"]): args = (TAG,) + tuple(args)
        el = G.call(e, args, 2.0)
except BaseException as ex:
    if isinstance(ex, KeyboardInterrupt): raise
    print(json.dumps({"ok":0,"why":"%%s: %%s" %% (type(ex).__name__, str(ex)[:80])}))
    raise SystemExit
if not isinstance(el, dict) or not el.get("anim"):
    print(json.dumps({"ok":0,"why":"anim မရှိ"})); raise SystemExit
# ⚠️⚠️ **motionkit ဖိုလ်ဒါသို့ ပြောင်းရမည်**。 `infogfx.OUT` က `work/<sub>`
#    (ဆွေမျိုး လမ်းကြောင်း) ဖြစ်ပြီး `rp()` က `G.MK` ကို ရှေ့တိုးသည် ⇒
#    chdir မလုပ်လျှင် PNG တွေက `~/ikki/work` ထဲ ရောက်ပြီး
#    `os.path.exists` က **အမြဲ False** ⇒ ဖရိမ်း တစ်ခုမှ မတိုင်ဖြစ်ဘဲ
#    「မှင် မလုံလောက်」 ထွက်သည် (၂၀၂၆-၁၀-၀၂ ဖမ်းမိ)。
def rp(q): return q if os.path.isabs(q) else os.path.join(G.MK, q)
_t = TH.t(); H, W = int(_t["H"]), int(_t["W"])
anim = list(el["anim"])
seq = list(anim[len(anim)//2:]) + [(q,x,y) for q,x,y,_d in el.get("statics",[])]

def _lin(v):
    v = v / 255.0
    return np.where(v <= 0.03928, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)

def _L(rgb):
    return (0.2126*_lin(rgb[...,0]) + 0.7152*_lin(rgb[...,1])
            + 0.0722*_lin(rgb[...,2]))

# \u26a0\ufe0f\u26a0\ufe0f **alpha \u1000 \u1005\u102c\u101e\u102c\u1038\u1014\u1032\u1037 \u1000\u1010\u103a\u1021\u1001\u103d\u1036\u1000\u102d\u102f \u1019\u1001\u103d\u1032\u1014\u102d\u102f\u1004\u103a\u1015\u102b**\u3002 \u1000\u1010\u103a\u1019\u103e\u102c
#    \u1014\u103e\u1005\u103a\u1001\u102f\u101c\u102f\u1036\u1038 alpha \u1041.\u1040 \u1016\u103c\u1005\u103a\u101e\u100a\u103a \u21d2 alpha \u1014\u1032\u1037 \u1001\u103d\u1032\u101c\u103b\u103e\u1004\u103a \u300c\u1019\u103e\u1004\u103a\u300d\u1000
#    \u1000\u1010\u103a\u1010\u1005\u103a\u1001\u102f\u101c\u102f\u1036\u1038 \u1016\u103c\u1005\u103a\u1015\u103c\u102e\u1038 \u1021\u1014\u102c\u1038\u1015\u1010\u103a\u101c\u100a\u103a\u1000 \u1018\u102e\u1012\u102e\u101a\u102d\u102f \u1016\u103c\u1005\u103a\u101e\u103d\u102c\u1038\u101e\u100a\u103a \u21d2
#    `qcard.num_point` \u1000 \u1041\u1045.\u1048\u1044:\u1041 \u1011\u103d\u1000\u103a\u1001\u1032\u1037\u101e\u100a\u103a (\u1010\u1000\u101a\u103a\u1010\u1019\u103a\u1038 \u1041.\u1047\u1045)\u3002
#    \u21d2 **\u1021\u101c\u1004\u103a\u1015\u102d\u1010\u103a \u1015\u102d\u102f\u1004\u103a\u1038\u1011\u1032 \u1021\u1000\u103d\u1000\u103a\u1021\u101c\u102d\u102f\u1000\u103a** \u1021\u101c\u1004\u103a\u1038 \u1016\u103d\u1032\u1037\u1005\u100a\u103a\u1038\u1015\u102f\u1036\u1000\u102d\u102f \u1000\u103c\u100a\u103a\u1037\u101e\u100a\u103a\u3002
BLK = 32
best = None
for it in seq:
    q = rp(it[0] if isinstance(it,(list,tuple)) else it)
    if not os.path.exists(q): continue
    im = Image.open(q).convert("RGBA")
    a = np.asarray(im).astype("float32")
    al = a[...,3] / 255.0
    solid = al >= 0.90
    if solid.sum() < 2000: continue
    L = _L(a[...,:3])
    h, w = L.shape
    hb, wb = h // BLK, w // BLK
    if hb < 2 or wb < 2: continue
    Lb = L[:hb*BLK, :wb*BLK].reshape(hb, BLK, wb, BLK).transpose(0,2,1,3)
    Sb = solid[:hb*BLK, :wb*BLK].reshape(hb, BLK, wb, BLK).transpose(0,2,1,3)
    Lf = Lb.reshape(hb*wb, BLK*BLK)
    Sf = Sb.reshape(hb*wb, BLK*BLK)
    full = Sf.all(axis=1)                 # ⚠️ အလင်းပိတ် အပြည့် ကွက်သာ
    if full.sum() < 4: continue
    Lf = Lf[full]
    hi = np.percentile(Lf, 90, axis=1)
    lo = np.percentile(Lf, 10, axis=1)
    rng = hi - lo
    # ⚠️ ဖွဲ့စည်းပုံ ရှိသော ကွက် (စာသား/ပုံ ပါသော) ကိုသာ — ပြားသော ကွက် မဟုတ်
    st = rng > 0.004
    if st.sum() < 3: continue
    rr = (hi[st] + 0.05) / (lo[st] + 0.05)
    # ⚠️ **အဆိုးဆုံး မယူရ** (noise) · **အကောင်းဆုံး မယူရ** (ဝါရောင် ဂဏန်း
    #    တစ်ခုက ကတ် တစ်ခုလုံးကို အောင်စေမည်) ⇒ ကွက်များရဲ့ **အလယ်မှတ်**
    r = float(np.median(rr))
    if best is None or r > best[0]:
        best = (r, float(st.sum()), float(np.percentile(rr, 10)),
                float(np.percentile(rr, 90)), int(solid.sum()))
if best is None:
    print(json.dumps({"ok":0,"why":"အလင်းပိတ် ကွက် မလုံလောက် (ပွင့်လင်း overlay)"}))
    raise SystemExit
print(json.dumps({"ok":1, "path": ("ikki" if kw is not None else "demo"),
                  "ratio": round(best[0],2), "blocks": int(best[1]),
                  "p10": round(best[2],2), "p90": round(best[3],2),
                  "solid_px": best[4]}))
''' % {"HERE": HERE}


def main(argv):
    import gfxcat as G
    fmt = "16:9"
    for a in argv[1:]:
        if a.startswith("--fmt="):
            fmt = a.split("=", 1)[1]
    js = os.path.join(HERE, "assets",
                      "gfx_contrast_%s.json" % fmt.replace(":", "x"))
    ids = [e["id"] for e in G.catalog()]
    if "--only" in argv:
        want = set(argv[argv.index("--only") + 1].split(","))
        ids = [i for i in ids if i in want]
    try:
        cache = json.load(open(js, encoding="utf-8")).get("items") or {}
    except (OSError, ValueError, AttributeError):
        cache = {}
    todo = [i for i in ids if "--force" in argv or i not in cache
            or not cache[i].get("ok")]
    print("── %s · တိုင်းမည် %d/%d ──" % (fmt, len(todo), len(ids)), flush=True)
    t0 = time.time()
    for k, eid in enumerate(todo, 1):
        try:
            r = subprocess.run([sys.executable, "-c", CHILD, eid, fmt],
                               capture_output=True, text=True, timeout=TIMEOUT)
            ln = [x for x in (r.stdout or "").strip().splitlines() if x.strip()]
            d = json.loads(ln[-1]) if ln else {}
            if not d.get("ok") and not d.get("why"):
                _er = [x for x in (r.stderr or "").strip().splitlines() if x.strip()]
                d["why"] = (_er[-1][:110] if _er else "stdout ဗလာ")
        except (subprocess.TimeoutExpired, ValueError, IndexError) as e:
            d = {"ok": 0, "why": type(e).__name__}
        cache[eid] = d
        try:
            import glob as _g
            for _dd in _g.glob(os.path.join(G.MK, "work", "*")):
                for _f in _g.glob(os.path.join(_dd, "*ct*")):
                    try:
                        os.remove(_f)
                    except OSError:
                        pass
        except Exception:
            pass
        json.dump({"version": 1, "fmt": fmt, "n": len(ids),
                   "_doc": "tools/gfxcontrast.py — စာသား ဖတ်နိုင်မှု "
                           "(WCAG ကွာခြားချက် · နောက်ခံ ၃ မျိုးရဲ့ အကောင်းဆုံး)",
                   "items": cache},
                  open(js, "w"), ensure_ascii=False, indent=1)
        if d.get("ok"):
            print("  [%3d/%3d] %-30s %6.2f:1%s"
                  % (k, len(todo), eid, d["ratio"],
                     "  ⚠️ ဖတ်မရ" if d["ratio"] < MIN_RATIO else ""), flush=True)
        else:
            print("  [%3d/%3d] %-30s ✖ %s"
                  % (k, len(todo), eid, str(d.get("why"))[:44]), flush=True)
    ok = {k: v for k, v in cache.items() if v.get("ok")}
    bad = sorted((v["ratio"], k) for k, v in ok.items() if v["ratio"] < MIN_RATIO)
    print("\n── ဖြန့်ကျက်မှု (%d ခု) ──" % len(ok))
    vs = sorted(v["ratio"] for v in ok.values())
    if vs:
        q = lambda p: vs[min(len(vs)-1, int(round(p*(len(vs)-1))))]
        print("  p10 %.2f · p25 %.2f · အလယ် %.2f · p75 %.2f · p90 %.2f"
              % (q(.1), q(.25), q(.5), q(.75), q(.9)))
    print("  ⚠️ %.1f : 1 အောက် **%d ခု**" % (MIN_RATIO, len(bad)))
    for r, i in bad[:25]:
        print("    %6.2f:1  %s" % (r, i))
    print("\n  ပြီး %.0fs" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
