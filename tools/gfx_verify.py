#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""motionkit template တစ်ခုချင်းကို **တကယ် render ပြီး** စစ်သည်。

⚠️ ဂိတ်ကို **ကိန်း မမြင်ခင်** သတ်မှတ်ထားသည် (၂၀၂၆-၀၉-၁၉):
     PASS = ① fill() က argument ထုတ်ပေးနိုင်
            ② call() က PNG **၂ ဖရိမ်း အနည်းဆုံး** ပြန်ပေး
            ③ ဖိုင်တိုင်း ရှိပြီး > 1 KB
            ④ **နောက်ဆုံး ဖရိမ်း မှာ မှင် ရှိ** — alpha>16 pixel က
               ဧရိယာ၏ **0.05% အထက်** (ဗလာ ဖရိမ်းကို ဖယ်ရန်)
            ⑤ 60s အတွင်း ပြီး
⚠️ တစ်ခုချင်း **သီးသန့် process** — အရင်က template တစ်ခု ကျလျှင်
   တစ်ခုလုံး ရပ်သွားခဲ့သည် (timeout · ctypes text trap)。
"""
import os, sys, json, subprocess, time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "core"))
TIMEOUT = 60
MIN_FRAMES = 2
# ⚠️ **ဖိုင် အရွယ် ဂိတ် မထားရ** — animation ရဲ့ ပထမ ဖရိမ်းများက ၁၃၃ bytes
#    (ဗလာနီးပါး) ဖြစ်တတ်သည် · ပုံမှန်。 >1KB ဟု ထားမိ၍ **အလုပ်လုပ်နေသော
#    template ၄၂ ခု** မှားကျခဲ့သည် (၂၀၂၆-၀၉-၁၉)。 မှင်ကို နောက်ဆုံး ဖရိမ်းမှာသာ စစ်。
MIN_BYTES = 1
MIN_INK = 0.0005          # 0.05%

CHILD = r'''
import os, sys, json
sys.path.insert(0, os.path.join(%(HERE)r, "core"))
import gfxcat as G, dress as DR
from PIL import Image
eid = sys.argv[1]
e = [x for x in G.catalog() if x["id"] == eid]
if not e: print(json.dumps({"ok":0,"why":"id မတွေ့"})); raise SystemExit
e = e[0]
# ⚠️ **engine ရဲ့ လမ်းကြောင်းအတိုင်း စစ်ရမည်** (၂၀၂၆-၀၉-၂၂)。 ယခင်က
#    `G.fill()` တစ်ခုတည်း စစ်ခဲ့သဖြင့် 「fill ဗလာ」 ၅၁ ခု ကျခဲ့သည် —
#    ဒါပေမယ့် engine က ယခု `tmplfit` ကိုပါ ပြန်ဆုတ်လမ်း အဖြစ် သုံးသည်
#    ⇒ verifier က engine ထက် **ကျဉ်း**နေလျှင် အသုံးဝင်သော template တွေကို
#    အလကား ပိတ်ထားရာ ကျသည်。
args = G.fill(e, "ဂျပန်မှာ အလုပ်", "ZAE", 62)
kw = None
# ⚠️ `fill()` က **param မလိုသော** template အတွက် `()` ပြန်ပေးသည် (မှန်သည် —
#    `gfxcat.fill` ကိုယ်တိုင် "`()` ပြန်ရမည်" ဟု ရေးထားပြီးသား)。 `if not args`
#    နဲ့ စစ်လျှင် `()` က falsy ဖြစ်၍ **ကျရှုံးဟု မှတ်**သည် ⇒ `trans` ၂၄/၂၄ ·
#    `motionfx` ၁၄ · `thm.chat_dots` တို့ တစ်ခါမှ မအောင်ခဲ့ (၂၀၂၆-၀၉-၂၄)。
if args is None:
    try:
        kw = DR._tf_args(dict(kind=eid, text="ဂျပန်မှာ အလုပ်ရှာဖွေခြင်း",
                              items=["ဂျပန်မှာ အလုပ်", "ပညာသင်", "ဗီဇာ"],
                              num="62"),
                         accent="#FFE000", ink="#FFFFFF", dim="#8B8B8B")
    except Exception as _e:
        kw = None
    if not kw:
        print(json.dumps({"ok":0,"why":"fill ဗလာ (tmplfit လည်း မရ)"})); raise SystemExit
if kw is not None:
    el = DR._call_template(getattr(__import__(e["module"]), e["fn"]),
                           eid, "g0", kw)
else:
    # ⚠️ production (dress.py) နှင့် **အတိအကျ တူရမည်** — tag ရှေ့က ထည့်
    if DR._wants_tag(e["fn"]): args = ("g0",) + tuple(args)
    el = G.call(e, args, 2.0)
if not isinstance(el, dict):
    print(json.dumps({"ok":0,"why":"dict မဟုတ် (%%s)" %% type(el).__name__})); raise SystemExit
fr = el.get("anim") or el.get("frames") or []
if len(fr) < %(MF)d:
    print(json.dumps({"ok":0,"why":"ဖရိမ်း %%d" %% len(fr)})); raise SystemExit
# ⚠️ လမ်းကြောင်းက motionkit cwd နှင့် ဆက်စပ် — MK အောက်မှ ဖတ်ရမည်
def rp(q): return q if os.path.isabs(q) else os.path.join(G.MK, q)
for it in fr:
    q = rp(it[0] if isinstance(it,(list,tuple)) else it)
    if not os.path.exists(q) or os.path.getsize(q) < %(MB)d:
        print(json.dumps({"ok":0,"why":"ဖိုင် သေး/မရှိ"})); raise SystemExit
# ⚠️ **နောက်ဆုံး ဖရိမ်းမှာ မှင် ရှိရမည်** ဆိုသော ဂိတ်က **မှား**သည် —
#    ထွက်ခွာ animation (`*_out` · `wipe_word` · `intro_stinger`) က နောက်ဆုံး
#    ဖရိမ်းမှာ ဗလာ ဖြစ်တာ **ဒီဇိုင်းအရ မှန်**သည်。 တိုင်းကြည့်ရာ
#    `kinetic2.pop_out` က အလယ်မှာ ၂၈.၃%% · နောက်ဆုံးမှာ ၀%% ⇒ ဂိတ်က
#    အလုပ်လုပ်နေသော template ၇ ခုကို မှားပိတ်ခဲ့သည် (၂၀၂၆-၀၉-၂၃)。
#    ⇒ နမူနာ ဖရိမ်းများထဲက **အမြင့်ဆုံး** မှင်ကို ယူသည်。
_cand = sorted(set([len(fr)-1, len(fr)//2, len(fr)//3, max(0,len(fr)-2), 1]))
ink = 0.0
for _k in _cand:
    if _k < 0 or _k >= len(fr): continue
    _it = fr[_k]
    _im = Image.open(rp(_it[0] if isinstance(_it,(list,tuple)) else _it)).convert("RGBA")
    _a = _im.split()[3]
    ink = max(ink, sum(1 for v in _a.getdata() if v > 16) / float(_im.width*_im.height))
im = _im
# ⚠️ **bbox ကိုပါ မှတ်ရမည်** — planner ရဲ့ pool ကို လက်ရေး ၃၀ ကနေ ၂၇၁+ သို့
#    ချဲ့လိုက်သဖြင့် 「ဂရပ်ဖစ်က စာတန်းကို ဖုံးသလား」ကို **တိုင်း**ရမည်。
#    `place.caption_band()` က keyword pop အတွက်သာ သုံးနေပြီး template event
#    ကို မစစ်ပါ (၂၀၂၆-၀၉-၂၂ စစ်၍ တွေ့)。 render ပြီးသား frame ရှိနေချိန်မှာ
#    တိုင်းလျှင် အပို render မလို。
# ⚠️ frame item က `(png, x, y)` — offset မထည့်လျှင် bbox လွဲမည်。
try:
    import numpy as _np
    _n = len(fr)
    _idx = sorted(set([_n-1, _n//2, max(0,_n-2), _n//3]))
    _b = []
    _W = _H = 0
    for _j in _idx:
        _it = fr[_j]
        _pp, _ox, _oy = (_it[0], _it[1], _it[2]) if isinstance(_it,(list,tuple)) and len(_it)>2 else (_it if isinstance(_it,str) else _it[0], 0, 0)
        _im = Image.open(rp(_pp)).convert("RGBA")
        _al = _np.array(_im)[:,:,3]
        _on = _al > 16
        if not _on.any(): continue
        _ys, _xs = _np.nonzero(_on)
        _b.append((_oy+int(_ys.min()), _oy+int(_ys.max()), _ox+int(_xs.min()), _ox+int(_xs.max())))
        _W = max(_W, _ox+_im.width); _H = max(_H, _oy+_im.height)
    # ⚠️ **ဘောင်အရွယ်ကို theme ကနေ ယူရမည်**。 element အများစုက ဘောင်အပြည့်
    #    PNG ပေမယ့် kinetic/capt/thm.type_* တို့က **strip** PNG ကို
    #    `(png, x, y)` နဲ့ ချသည် — strip ရဲ့ အောက်စွန်းနဲ့ စားလျှင် အချိုး
    #    ဖောင်းပြီး 「စာတန်းဇုန် ဖုံးသည်」ဟု **မှားပြ**မည်
    #    (thm.type_word: တကယ် ၀.၄၅ · စား၍ ၀.၈၅ — ၂၀၂၆-၀၉-၂၄ တွေ့)。
    try:
        import theme as _TH
        _tt = _TH.t(); _W, _H = int(_tt["W"]), int(_tt["H"])
    except Exception:
        pass
    _bb = None
    if _b and _W and _H:
        _bb = dict(top=round(min(x[0] for x in _b)/_H,4), bottom=round(max(x[1] for x in _b)/_H,4),
                   left=round(min(x[2] for x in _b)/_W,4), right=round(max(x[3] for x in _b)/_W,4))
except Exception:
    _bb = None
print(json.dumps({"ok": 1 if ink >= %(MI)f else 0,
                  "why": "" if ink >= %(MI)f else "မှင် %%.4f%%%%" %% (ink*100),
                  "ink": round(ink,5), "n": len(fr), "bbox": _bb}))
''' % {"HERE": HERE, "MF": MIN_FRAMES, "MB": MIN_BYTES, "MI": MIN_INK}

def main():
    import gfxcat as G
    only = os.environ.get("GFX_ONLY")
    # ⚠️ `usable()` က `USE` အမျိုးအစားသာ ပြန်ပေး ⇒ `mockup` · `transition` ·
    #    `motion` (၁၁၃ ခု) ကို **စစ်တောင် မစစ်ဖြစ်**ခဲ့。 "IKKI ကို ၁၀၀%
    #    ပေး" ဆိုလျှင် အရင်ဆုံး အဲဒါတွေ render ဖြစ်မဖြစ် သိရမည် ⇒ `GFX_ALL=1`。
    ents = G.catalog() if os.environ.get("GFX_ALL") else G.usable()
    if only: ents = [e for e in ents if e["id"] in only.split(",")]
    print(f"စစ်မည် {len(ents)} ခု · timeout {TIMEOUT}s", flush=True)
    res, t0 = [], time.time()
    for i, e in enumerate(ents, 1):
        r = {"id": e["id"], "category": e["category"]}
        try:
            p = subprocess.run([sys.executable, "-c", CHILD, e["id"]],
                               capture_output=True, text=True, timeout=TIMEOUT)
            out = (p.stdout or "").strip().splitlines()
            j = json.loads(out[-1]) if out else {"ok": 0, "why": "ထွက်ချက် ဗလာ"}
            r.update(j)
            if not j.get("ok") and not j.get("why"):
                r["why"] = (p.stderr or "")[-120:]
        except subprocess.TimeoutExpired:
            r.update({"ok": 0, "why": f"{TIMEOUT}s ကျော်"})
        except Exception as ex:
            r.update({"ok": 0, "why": f"{type(ex).__name__}: {ex}"})
        res.append(r)
        mark = "✓" if r.get("ok") else "✖"
        print(f"  [{i:3d}/{len(ents)}] {mark} {e['id']:34s} {r.get('why','')[:60]}", flush=True)
    ok = [r for r in res if r.get("ok")]
    print(f"\nအောင် {len(ok)}/{len(res)} · {time.time()-t0:.0f}s", flush=True)
    # ⚠️ **`GFX_ONLY` နဲ့ ပြေးလျှင် ဖိုင်ကို မလွှမ်းရ** — ၂၀၂၆-၀၉-၂၂:
    #    template ၂ ခု spot-check လုပ်ရာ ၁၇၂ entry ဖိုင်ကို ၂ entry နဲ့
    #    လွှမ်းပစ်ခဲ့သည် (git ကနေ ပြန်ယူရ)。 ⇒ အပိုင်း ပြေးလျှင် **ပေါင်း**သည်。
    _p = os.path.join(HERE, "assets", "gfx_verify.json")
    if only:
        old = []
        try:
            old = json.load(open(_p, encoding="utf-8")) or []
        except Exception:
            old = []
        _new = {r["id"]: r for r in old}
        _new.update({r["id"]: r for r in res})
        res_all = sorted(_new.values(), key=lambda r: r["id"])
        print(f"  (အပိုင်း ပြေးပြီး — ရှိပြီးသား {len(old)} နဲ့ ပေါင်း ⇒ "
              f"{len(res_all)})", flush=True)
    else:
        res_all = res
    json.dump(res_all, open(_p, "w"), ensure_ascii=False, indent=1)
    from collections import Counter
    print("module အလိုက် အောင်:", dict(Counter(r["id"].split(".")[0] for r in ok)))

if __name__ == "__main__":
    main()
