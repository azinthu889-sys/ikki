#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""template တစ်ခုချင်း၏ **တကယ့် အမြင့်** ကို တိုင်းသည် (Overlay audit P0)

⚠️ တကယ့် headtop render မှာ ဂရပ်ဖစ် ၇ ခု ရွေးပြီး **၀–၃ ခုသာ** တပ်ဖြစ်ခဲ့သည် —
   စကားပြောသူက ဘောင်ရဲ့ အပေါ် ၆၄% ဖုံးပြီး အောက်က စာတန်းက ယူထားလို့
   **၆၁ px သာ** ကျန်သည်。 ကတ်တွေက ၅၂၈–၁၀၇၇ px မြင့်၍ တစ်ခုမှ မဝင်ပါ。
⚠️ ဒါကို **ဆောက်ပြီးမှ** သိရသဖြင့် အချိန် ကုန်ပြီး ဂရပ်ဖစ် မရှိတော့。
   ⇒ အမြင့်ကို **ကြိုတိုင်းထား**ပြီး ရွေးချိန်မှာ စစ်ရမည်。
⚠️ တိုင်းနည်းက `dress._ybox()` နဲ့ **အတူတူ** ဖြစ်ရမည် — မတူလျှင် ကြိုတိုင်းချက်
   က အလကား (ရွေးပြီးမှ ပယ်ခံရဦးမည်)。 ⇒ anim ရဲ့ **နောက်ပိုင်းတစ်ဝက်** နဲ့
   statics ကို ပေါင်းပြီး alpha bbox ယူသည်。
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "core"))
TIMEOUT = 75

CHILD = r'''
import os, sys, json
sys.path.insert(0, os.path.join(%(HERE)r, "core"))
import gfxcat as G, dress as DR, formats as FM
# \u26a0\ufe0f `theme` \u1000 motionkit \u101b\u1032 module \u2014 core/ \u1011\u1032 \u1019\u101f\u102f\u1010\u103a \u21d2 MK \u1000\u102d\u102f path \u1011\u1032 \u1011\u100a\u103a\u1037\u1019\u103e \u101b
if G.MK not in sys.path: sys.path.insert(0, G.MK)
import theme as TH
import numpy as np
from PIL import Image
eid = sys.argv[1]
fmt = sys.argv[2] if len(sys.argv) > 2 else "16:9"
# \u26a0\ufe0f **production \u1014\u1032\u1037 \u1021\u1010\u102d\u1021\u1000\u103b \u1010\u1030\u100a\u102e\u101e\u1031\u102c \u1018\u1031\u102c\u1004\u103a\u1021\u101b\u103d\u101a\u103a \u1016\u103c\u1005\u103a\u101b\u1019\u100a\u103a**\u3002 motionkit \u101b\u1032
#    \u1015\u102f\u1036\u101e\u1031 (1080\u00d71440) \u1014\u1032\u1037 \u1010\u102d\u102f\u1004\u103a\u1038\u101c\u103b\u103e\u1004\u103a box_call \u1000 \u1042\u1040.\u1047%% \u1011\u103d\u1000\u103a\u1015\u103c\u102e\u1038
#    production (1920\u00d71080) \u1019\u103e\u102c \u1044\u1048.\u1049%% \u2014 \u1010\u102d\u102f\u1004\u103a\u1038\u1001\u103b\u1000\u103a\u1000 \u1021\u101c\u1000\u102c\u1038 \u1016\u103c\u1005\u103a\u101e\u100a\u103a\u3002
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
if DR._wants_tag(e["fn"]): args = ("g0",) + tuple(args)
el = G.call(e, args, 2.0)
if not isinstance(el, dict):
    print(json.dumps({"ok":0,"why":"dict မဟုတ်"})); raise SystemExit
def rp(q): return q if os.path.isabs(q) else os.path.join(G.MK, q)
# ⚠️ `dress._ybox()` နဲ့ အတူတူ — anim ရဲ့ နောက်ပိုင်းတစ်ဝက် + statics
anim = list(el.get("anim") or [])
if len(anim) < 2:
    print(json.dumps({"ok":0,"why":"ဖရိမ်း %%d" %% len(anim)})); raise SystemExit
seq = list(anim[len(anim)//2:]) + [(q,x,y) for q,x,y,_d in el.get("statics",[])]
y0, y1, x0, x1, H, W = 10**9, -1, 10**9, -1, 0, 0
for it in seq:
    q = rp(it[0] if isinstance(it,(list,tuple)) else it)
    if not os.path.exists(q): continue
    im = Image.open(q).convert("RGBA")
    W = max(W, im.width); H = max(H, im.height)
    a = np.asarray(im)[:,:,3]
    ys = np.nonzero(a.max(axis=1) > 8)[0]
    xs = np.nonzero(a.max(axis=0) > 8)[0]
    if len(ys):
        oy = it[2] if isinstance(it,(list,tuple)) and len(it) > 2 else 0
        ox = it[1] if isinstance(it,(list,tuple)) and len(it) > 1 else 0
        y0 = min(y0, oy+int(ys.min())); y1 = max(y1, oy+int(ys.max()))
        x0 = min(x0, ox+int(xs.min())); x1 = max(x1, ox+int(xs.max()))
if y1 < 0 or not H:
    print(json.dumps({"ok":0,"why":"မှင် မရှိ"})); raise SystemExit
# \u26a0\ufe0f **\u1021\u1001\u103b\u102d\u102f\u1038\u1000\u102d\u102f element canvas \u1014\u1032\u1037 \u1019\u1010\u103d\u1000\u103a\u101b** \u2014 `word_pop` \u101b\u1032 canvas \u1000 \u1041\u1049\u1047px 
#    \u1016\u103c\u1005\u103a\u101e\u1016\u103c\u1004\u103a\u1037 \u1041\u1042\u1042/\u1041\u1049\u1047 = \u1046\u1042%% \u1011\u103d\u1000\u103a\u1015\u103c\u102e\u1038 \u1010\u1000\u101a\u103a\u1010\u1019\u103a\u1038\u1000 \u1018\u1031\u102c\u1004\u103a\u101b\u1032\u1037 \u1041\u1041%% \u101e\u102c\u3002
#    \u21d2 **production \u1018\u1031\u102c\u1004\u103a\u1021\u1019\u103c\u1004\u103a\u1037** (theme \u101b\u1032 H) \u1000\u102d\u102f \u1021\u1001\u103c\u1031\u1001\u1036 \u1011\u102c\u1038\u101e\u100a\u103a\u3002
_d = TH.t()
print(json.dumps({"ok":1, "h": int(y1-y0), "w": int(max(0,x1-x0)),
                  "H": int(_d["H"]), "W": int(_d["W"]),
                  "canvas_h": int(H), "canvas_w": int(W), "n": len(anim)}))
''' % {"HERE": HERE}


def main(argv):
    import gfxcat as G
    import dress as DR
    # \u26a0\ufe0f format \u1021\u101c\u102d\u102f\u1000\u103a \u1010\u102d\u102f\u1004\u103a\u1038\u101b\u1019\u100a\u103a \u2014 16:9 \u1014\u1032\u1037 9:16 \u1019\u103e\u102c \u1021\u1019\u103c\u1004\u103a\u1037 \u1019\u1010\u1030
    fmt = "16:9"
    for a in argv[1:]:
        if a.startswith("--fmt="):
            fmt = a.split("=", 1)[1]
    want = [a for a in argv[1:] if not a.startswith("-")]
    # ⚠️⚠️ **bare fn ကြားခံ ဖယ်ပြီး catalog ကနေ တိုက်ရိုက် ယူသည်**。
    #    အရင်က `DR._verified()` (fn နာမည်) → `idx[fn]` → id ဆိုပြီး
    #    ကြားခံ ၂ ဆင့် ရှိခဲ့သည် ⇒ (၁) နာမည် ထပ်သူ ၂၁ ခုမှာ **ပထမ module
    #    တစ်ခုတည်း** ကျန်ပြီး ကျန် ၂၃ ခု ပျောက် · (၂) `_verified()` ဗလာ
    #    ဖြစ်လျှင် `ids` ဗလာ ⇒ **「၀ ခု」ပြေးပြီး ဖိုင် ဗလာ ရေးချ**သည်
    #    (၂၀၂၆-၀၉-၂၆: ဤအတိုင်း ၅၉၃ entry ပျက်ခဲ့)。
    ids = [(e["fn"], e["id"]) for e in G.catalog()]
    if want:
        # ⚠️ **fn နာမည် ရော id ရော လက်ခံရမည်** — `insert.insert_label` လို
        #    id ပေးလျှင် `w in f` (fn သာ) က မတိုက်ဘဲ **၀ ခု** ဖြစ်ပြီး
        #    ဗလာဖိုင် ရေးမိသည် (၂၀၂၆-၀၉-၂၁ ဖမ်းမိ)。
        ids = [(f, i) for f, i in ids
               if any(w == f or w == i or w in f or w in i for w in want)]
    out, t0 = {}, time.time()
    print(f"── template {len(ids)} ခု တိုင်းသည် ──")
    for k, (fn, eid) in enumerate(ids):
        try:
            r = subprocess.run([sys.executable, "-c", CHILD, eid, fmt],
                               capture_output=True, text=True, timeout=TIMEOUT)
            d = json.loads((r.stdout or "{}").strip().splitlines()[-1])
        except (subprocess.TimeoutExpired, ValueError, IndexError) as e:
            d = {"ok": 0, "why": type(e).__name__}
        # ⚠️⚠️ **key ကို `module.fn` အပြည့် (id) နဲ့ လုပ်ရမည်**。 `out[fn]` နဲ့
        #    bare fn သုံးခဲ့သဖြင့် နာမည် ထပ်သူများ **အပြန်အလှန် လွှမ်း**ခဲ့သည် —
        #    ၂၀၂၆-၀၉-၂၆ တိုင်းချက်: ထပ်သူ fn ၂၁ ခု → template ၄၄ ခု ဖုံး ·
        #    ဖိုင်ထဲ entry ၂၁ သာ ⇒ **template ၂၃ ခုရဲ့ ဒေတာ ဖျက်ခံရ**。
        #    အဆိုးဆုံးက `chat_thread` (mockups vs thm) · `tag_pill`
        #    (qcard vs thm) — အရွယ် တကယ် ကွဲသင့်သူတွေ ဖြစ်ခြင်း。
        #    (`dress._CIDX` က `fn` နဲ့ key လုပ်တဲ့ အမှားနဲ့ **အတန်း တူ**)
        if d.get("ok"):
            H = float(d["H"]) or 1080.0
            out[eid] = dict(h=d["h"], w=d["w"], H=d["H"], W=d["W"],
                            h_pct=round(d["h"] / H, 4),
                            w_pct=round(d["w"] / float(d["W"] or 1920), 4))
        else:
            out[eid] = dict(err=d.get("why", "?"))
        if (k + 1) % 20 == 0 or k + 1 == len(ids):
            okn = sum(1 for v in out.values() if "h_pct" in v)
            print(f"  {k+1:3}/{len(ids)} · ရ {okn} · {time.time()-t0:.0f}s", flush=True)
    tag = fmt.replace(":", "x")
    p = os.path.join(HERE, "assets", f"gfx_size_{tag}.json")
    # ⛔ **ဗလာ ရလဒ်နဲ့ ရေးမချရ** — ရှိပြီးသား ဒေတာ ဖျက်မိမည်。
    #    ၂၀၂၆-၀၉-၂၁ မှာ comment ရေးထားပြီးသား ဖြစ်လျက် guard မထည့်ခဲ့၍
    #    ၂၀၂၆-၀၉-၂၆ မှာ entry ၅၉၃ ခု တကယ် ပျက်ခဲ့သည်。
    if not out:
        print("  ⛔ ရလဒ် ၀ ခု — ဖိုင် မရေးပါ (ရှိပြီးသား ဒေတာ မဖျက်ရ)")
        print("     want=%r · catalog=%d" % (want, len(G.catalog())))
        return 1
    # ⚠️ အပိုင်းလိုက် ပြေးလျှင် **ပေါင်းရမည်** — လွှမ်းလျှင် ကျန်တာ ပျောက်
    if want:
        try:
            _old = json.load(open(p, encoding="utf-8")).get("items") or {}
            _old.update(out); out = _old
            print("  (အပိုင်း — ရှိပြီးသားနဲ့ ပေါင်း ⇒ %d)" % len(out))
        except Exception:
            pass
    # ⛔ **key ပုံစံ ၂ မျိုး မရောစေရ** — `module.fn` (id) သာ。 bare fn ရောလျှင
    #    `dress._CIDX` က မတွေ့ဘဲ ကျော်မည် ⇒ ရှိပြီးသား ဒေတာ အသုံးမဝင်。
    _bare = sorted(k for k in out if "." not in k)
    if _bare:
        print("  ⛔ key ပုံစံ ရောနေသည် — bare fn %d ခု: %s"
              % (len(_bare), ", ".join(_bare[:8])))
        print("     `module.fn` (id) သာ လက်ခံသည် ⇒ ဖိုင် မရေးပါ")
        return 1
    # ⛔ **ကျုံ့မှု guard** (Zin ၂၀၂၆-၀၉-၂၆)。 ဗလာ guard က `593 → 4` ကို
    #    **မဖမ်း**ပါ (၄ ခု ရှိသည်) ⇒ အရေအတွက် ကျုံ့လျှင် ရပ်ရမည်。
    _prev = {}
    try:
        _prev = json.load(open(p, encoding="utf-8")).get("items") or {}
    except Exception:
        pass
    if len(out) < len(_prev) and "--shrink-ok" not in argv:
        _lost = sorted(set(_prev) - set(out))
        print("  ⛔ **ကျုံ့မှု** — ရှိပြီးသား %d ခု → အသစ် %d ခု (ပျောက် %d)"
              % (len(_prev), len(out), len(_lost)))
        print("     ပျောက်မယ့် key: %s%s"
              % (", ".join(_lost[:12]), " …" if len(_lost) > 12 else ""))
        print("     တမင် ဆိုလျှင် `--shrink-ok` ထည့်ပါ ⇒ ဖိုင် မရေးပါ")
        return 1
    # ⚠️ **atomic ရေးရမည်** — ကြားထဲ ပြတ်လျှင် ဖိုင် တစ်ဝက် ကျန်ခဲ့မည်。
    _tmp = p + ".tmp%d" % os.getpid()
    with open(_tmp, "w", encoding="utf-8") as f:
        json.dump(dict(version=2, fmt=fmt, n=len(out),
                       _doc="⚠️ `h_pct` က ဘောင်အမြင့်ရဲ့ အချိုး — "
                            "`dress._ybox()` နဲ့ တူညီသော နည်းနဲ့ တိုင်းထားသည်。",
                       items=out), f, ensure_ascii=False, indent=0)
        f.flush()
        os.fsync(f.fileno())
    os.replace(_tmp, p)
    # ⚠️ **ဘယ်သူ ရေးလဲ မှတ်ရမည်** — ၂၀၂၆-၀၉-၂၆ မှာ entry ၅၉၃ ခု
    #    ဖျက်ခံရပြီး **ဘယ် session ဖျက်မိလဲ ရှာ၍ မရ**ခဲ့သည်。
    try:
        _pv = p[:-len(".json")] + ".prov.json"
        with open(_pv, "w", encoding="utf-8") as f:
            json.dump(dict(writer=os.path.abspath(sys.argv[0]),
                           argv=list(argv[1:]), ts=time.time(),
                           when=time.strftime("%Y-%m-%d %H:%M:%S"),
                           n=len(out), n_prev=len(_prev),
                           subset=bool(want), pid=os.getpid()),
                      f, ensure_ascii=False, indent=1)
    except Exception as _pe:
        print("  ⚠️ prov မရေးရ (%s)" % type(_pe).__name__)
    got = {k: v for k, v in out.items() if "h_pct" in v}
    print(f"\n  ရလဒ် {len(got)}/{len(out)} → {os.path.basename(p)} ({fmt})")
    if got:
        hs = sorted(v["h_pct"] for v in got.values())
        n = len(hs)
        print(f"  အမြင့် p10 {hs[n//10]:.1%} · အလယ် {hs[n//2]:.1%} · p90 {hs[9*n//10]:.1%}")
        for lim in (0.06, 0.12, 0.20, 0.35):
            print(f"    ≤{lim:.0%}H ဝင်ဆံ့: {sum(1 for h in hs if h <= lim):3} ခု")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
