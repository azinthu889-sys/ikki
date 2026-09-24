#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**ဖြတ်ပြောင်း (cutaway) ဖြစ်နိုင်သူ**ကို alpha အလယ်မှတ်နဲ့ တိုင်းသည်。

    python3 tools/gfx_cutaway.py [--only id,id] [--write]

⚠️ **`assets/gfx_fullstage.txt` ကို မယုံရ**。 အဲဒါက `gfx_verify.json` ရဲ့
   `bbox` ကနေ ထုတ်ထားပြီး `bbox` က **alpha > ၁၆** pixel ကို ရေတွက်သည် ⇒
   ၇% အလင်းပိတ် နောက်ခံ လွှာလေးကိုပင် 「ဘောင်အပြည့်」ဟု မှတ်သည်。
   ၂၀၂၆-၀၉-၂၄ တိုင်းရာ — ၃၉ ခုမှာ ၃၀ ခုက `ink` **၁.၀၀၀၀ တိတိ** ·
   bbox လည်း အားလုံး `0.0→0.9993` တစ်ထပ်တည်း。 မတူသော template ၃၀ ခု
   ဒဿမ ၄ လုံးအထိ ညီတာက **တိုင်းချက် ပျက်နေခြင်း** ဖြစ်သည်。
⚠️ ဖြတ်ပြောင်း ဆိုသည်မှာ **ပြောသူကို တကယ် ဖုံး**ရမည် ⇒ တိုင်းရမည့် ကိန်းက
   `alpha` ရဲ့ **အလယ်မှတ်** (ဖုံးအုပ်မှု အမှန်)、pixel ရေတွက်ချက် မဟုတ်。
   စာတန်း template (`prem5.karaoke_cap` စသည်) က bbox ဘောင်အပြည့် ဖြစ်ပေမယ့်
   alpha အလယ်မှတ် နိမ့်သည် — အဲဒါက ဖြတ်ပြောင်း **မဟုတ်**、စာတန်း ဖြစ်သည်。
⚠️ ဂိတ် ကိန်းကို **ဖြန့်ကျက်မှု မကြည့်ခင် မသတ်မှတ်ရ** — `--write` မပါလျှင်
   တိုင်းချက်သာ ပြသည်。
"""
import os, sys, json, subprocess, time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "core"))
TIMEOUT = 150
FS = os.path.join(HERE, "assets", "gfx_fullstage.txt")
OUT = os.path.join(HERE, "assets", "gfx_cutaway.txt")
JS = os.path.join(HERE, "assets", "gfx_cutaway.json")
COVER_MIN = 0.85          # ⚠️ ဖြန့်ကျက်မှု ကြည့်ပြီးမှ တွေ့ရသော ကန့်သတ်

CHILD = r'''
import os, sys, json
sys.path.insert(0, os.path.join(%(HERE)r, "core"))
import gfxcat as G, dress as DR
from PIL import Image
eid = sys.argv[1]
e = [x for x in G.catalog() if x["id"] == eid]
if not e: print(json.dumps({"ok":0,"why":"id မတွေ့"})); raise SystemExit
e = e[0]
args = G.fill(e, "ဂျပန်မှာ အလုပ်", "ZAE", 62)
kw = None
if args is None:
    try:
        kw = DR._tf_args(dict(kind=eid, text="ဂျပန်မှာ အလုပ်ရှာဖွေခြင်း",
                              items=["ဂျပန်မှာ အလုပ်", "ပညာသင်", "ဗီဇာ"],
                              num="62"),
                         accent="#FFE000", ink="#FFFFFF", dim="#8B8B8B")
    except Exception:
        kw = None
    if not kw:
        print(json.dumps({"ok":0,"why":"fill ဗလာ"})); raise SystemExit
# ⚠️ ခေါ်နည်းက `tools/gfx_verify.py` နဲ့ **အတိအကျ တူရမည်** — `G.call` က
#    `(entry, args, dur)` ယူသည်、tag ကို ရှေ့ဆုံးမှာ ထည့်ရသည်、factory
#    closure တွေက `BUILDERS` ထဲမှာသာ ရှိသည်。
try:
    if kw is not None:
        _m = __import__(e["module"])
        _fn = getattr(_m, "BUILDERS", {}).get(e["fn"]) or getattr(_m, e["fn"])
        el = DR._call_template(_fn, eid, "g0", kw)
    else:
        import hashlib as _h
        _tag = "v" + _h.sha1(eid.encode()).hexdigest()[:8]
        if DR._wants_tag(e["fn"]): args = (_tag,) + tuple(args)
        el = G.call(e, args, 2.0)
except BaseException as ex:
    if isinstance(ex, KeyboardInterrupt): raise
    print(json.dumps({"ok":0,"why":"%%s: %%s" %% (type(ex).__name__, str(ex)[:90])}))
    raise SystemExit
if not isinstance(el, dict):
    print(json.dumps({"ok":0,"why":"dict မဟုတ်"})); raise SystemExit
# ⚠️ **`statics` ကို ဦးစားပေးရမည်** — `anim` က ဝင်/ထွက် ဖရိမ်းများ ဖြစ်ပြီး
#    `statics` က **ရပ်နေချိန် အလင်းပိတ် အပြည့်** ဖရိမ်း ဖြစ်သည်
#    (`core/dress.py`)。 `anim` ကိုသာ တိုင်းလျှင် ဖုံးအုပ်မှု လျော့ပြမည်。
fr = list(el.get("statics") or []) + list(el.get("anim") or el.get("frames") or [])
if len(fr) < 1:
    print(json.dumps({"ok":0,"why":"ဖရိမ်း မလုံလောက်"})); raise SystemExit
def rp(q): return q if os.path.isabs(q) else os.path.join(G.MK, q)
try:
    import theme as _TH
    _tt = _TH.t(); _W, _H = int(_tt["W"]), int(_tt["H"])
except Exception:
    _W = _H = 0
import numpy as _np
# ⚠️ **ဖရိမ်း အားလုံး မတိုင်းရ** — ဝင်/ထွက် ဖရိမ်းတွေက ဖေးဖေး ဖြစ်သဖြင့်
#    ပျမ်းမျှ ယူလျှင် နိမ့်သွားမည်。 ရပ်နေချိန် (**အမြင့်ဆုံး**) ကို ယူသည်。
_n = len(fr)
_idx = sorted(set([_n//2, _n//3, 2*_n//3, max(0,_n-2), _n-1]))
best = 0.0
for _j in _idx:
    if _j < 0 or _j >= _n: continue
    _it = fr[_j]
    _pp, _ox, _oy = ((_it[0], _it[1], _it[2])
                     if isinstance(_it,(list,tuple)) and len(_it) > 2
                     else ((_it if isinstance(_it,str) else _it[0]), 0, 0))
    _im = Image.open(rp(_pp)).convert("RGBA")
    _al = _np.array(_im)[:,:,3].astype("float32") / 255.0
    if _W and _H:
        # ⚠️ strip PNG က ဘောင်တစ်ခုလုံး မဟုတ် ⇒ **ဘောင်အပြည့်ပေါ် ချ**ပြီးမှ
        #    အလယ်မှတ် ယူရမည်、မဟုတ်လျှင် strip သေးလေ ဖုံးအုပ်မှု မြင့်လေ
        #    ဖြစ်ကာ 「စာတန်းက ဖြတ်ပြောင်း」ဟု မှားမည်。
        _cv = _np.zeros((_H, _W), dtype="float32")
        _y1 = min(_H, _oy + _al.shape[0]); _x1 = min(_W, _ox + _al.shape[1])
        if _y1 > _oy and _x1 > _ox:
            _cv[_oy:_y1, _ox:_x1] = _al[:_y1-_oy, :_x1-_ox]
        _al = _cv
    best = max(best, float(_al.mean()))
print(json.dumps({"ok":1, "cover": round(best, 4), "n": _n}))
''' % {"HERE": HERE}


def main():
    ids = [l.strip() for l in open(FS, encoding="utf-8")
           if l.strip() and not l.startswith("#")]
    if "--only" in sys.argv:
        want = set(sys.argv[sys.argv.index("--only") + 1].split(","))
        ids = [i for i in ids if i in want]
    # ⚠️ **တိုင်းပြီးသားကို cache ကနေ ယူရမည်** — ၂၀၂၆-၀၉-၂၄: တစ်ခုစီ ~၃၅s
    #    ကြာသဖြင့် ၃၉ ခုက ~၂၀ မိနစ် လိုသည်。 ၂၁/၃၉ မှာ process ရပ်သွားရာ
    #    တိုင်းချက် ၂၁ ခု **အလဟဿ** ဖြစ်ခဲ့ (ဖိုင် အဆုံးမှသာ ရေးသဖြင့်)。
    #    ⇒ တစ်ခုပြီးတိုင်း သိမ်း · ရှိပြီးသားကို ကျော် (`--force` နဲ့ အတင်း)。
    try:
        cache = {r["id"]: r for r in json.load(open(JS, encoding="utf-8"))}
    except (OSError, ValueError, KeyError, TypeError):
        cache = {}
    force = "--force" in sys.argv
    todo = [i for i in ids if force or i not in cache
            or not isinstance(cache[i].get("cover"), float)]
    print(f"တိုင်းမည် {len(todo)}/{len(ids)} ခု (cache {len(cache)}) · "
          f"alpha အလယ်မှတ် (ဖုံးအုပ်မှု အမှန်)", flush=True)
    res = [cache[i] for i in ids if i not in todo and i in cache]
    t0 = time.time()
    for k, i in enumerate(todo, 1):
        r = {"id": i}
        try:
            p = subprocess.run([sys.executable, "-c", CHILD, i],
                               capture_output=True, text=True, timeout=TIMEOUT)
            out = (p.stdout or "").strip().splitlines()
            r.update(json.loads(out[-1]) if out else
                     {"ok": 0, "why": (p.stderr or "")[-100:]})
        except subprocess.TimeoutExpired:
            r.update({"ok": 0, "why": f"{TIMEOUT}s ကျော်"})
        except Exception as ex:
            r.update({"ok": 0, "why": f"{type(ex).__name__}: {ex}"})
        # ⚠️ **template တစ်ခုပြီးတိုင်း ယာယီ frame ရှင်းရမည်** — ၂၀၂၆-၀၉-၂၄:
        #    ရှင်းချက် မထည့်မိသဖြင့် ၁၆ ခု ပြေးပြီးမှာ `motionkit/work` က
        #    ၁.၀ GB ရောက်ပြီး disk လွတ်နေတာ ၁.၉ GB သာ ကျန်ခဲ့သည်。
        #    (`tools/gfx_verify.py` မှာ ရှိပြီးသား — ကူးမိမှ မကူးမိ)。
        # ⚠️ `work/` တစ်ခုလုံး မဖျက်ရ — ဤ id ရဲ့ tag နဲ့ ကိုက်တာကိုသာ。
        try:
            import glob as _g, hashlib as _hh
            import gfxcat as _G
            _t = "v" + _hh.sha1(i.encode()).hexdigest()[:8]
            for _d in _g.glob(os.path.join(_G.MK, "work", "*")):
                for _f in _g.glob(os.path.join(_d, "*%s*" % _t)):
                    try:
                        os.remove(_f)
                    except OSError:
                        pass
        except Exception:
            pass
        res.append(r)
        # ⚠️ **တစ်ခုပြီးတိုင်း ရေးသည်** — ရပ်သွားလည် တိုင်းချက် မပျောက်ရ
        cache[i] = r
        json.dump(sorted(cache.values(), key=lambda x: x["id"]),
                  open(JS, "w"), ensure_ascii=False, indent=1)
        c = r.get("cover")
        print(f"  [{k:2d}/{len(todo)}] {i:28s} "
              + (f"ဖုံးအုပ်မှု {c*100:6.2f}%" if isinstance(c, float)
                 else f"✖ {r.get('why','')[:50]}"), flush=True)
    good = sorted((r for r in res if isinstance(r.get("cover"), float)),
                  key=lambda r: -r["cover"])
    print(f"\n── ဖြန့်ကျက်မှု ({len(good)} ခု) ──")
    for r in good:
        bar = "█" * int(r["cover"] * 40)
        print(f"  {r['cover']*100:6.2f}%  {r['id']:28s} {bar}")
    keep = [r["id"] for r in good if r["cover"] >= COVER_MIN]
    print(f"\nဖြတ်ပြောင်း အဖြစ် သုံးနိုင် **{len(keep)}/{len(res)}** "
          f"(ဖုံးအုပ်မှု ≥ {COVER_MIN*100:.0f}%) · {time.time()-t0:.0f}s")
    if "--write" in sys.argv:
        with open(OUT, "w", encoding="utf-8") as f:
            f.write("# **ဖြတ်ပြောင်း (cutaway)** — ပြောသူကို တကယ် ဖုံးသူ。\n")
            f.write(f"# ထုတ်သူ: tools/gfx_cutaway.py — alpha အလယ်မှတ် "
                    f"≥ {COVER_MIN*100:.0f}% (မှန်းမရေး)。\n")
            f.write("# ⚠️ `gfx_fullstage.txt` က bbox ကနေ ⇒ စာတန်း template "
                    "တွေပါ ပါသည်。 ဤဖိုင်ကိုသာ planner က သုံးသည်。\n")
            for i in keep:
                f.write(i + "\n")
        print(f"ရေးပြီး — {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
