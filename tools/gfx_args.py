#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""စာရင်း (list) argument ယူသော template များအတွက် **အလုပ်ဖြစ်တဲ့ ပုံစံ** ရှာသည်。

⚠️ ပုံစံကို **မှန်းဆ၍ မရ** — template တစ်ခုချင်း မတူ (2-tuple · string ·
   3-tuple · dict)。 ⇒ ပုံစံတိုင်းကို **တကယ် render ပြီး** စစ်သည်。
⚠️ အောင်တယ်လို့ သတ်မှတ်ချက်က `gfx_verify.py` နဲ့ **အတူတူ** —
   ဖရိမ်း ≥၂ · ဖိုင် ရှိ · နောက်ဆုံး ဖရိမ်းမှာ မှင် ≥၀.၀၅%。
ထွက်: assets/gfx_args.json  {template_id: shape}
"""
import os, sys, json, subprocess


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── W-1…W-4 လုံခြုံ ရေးမှု (`core/derived_io.py`) ─────────────────────
# ⚠️ ၂၀၂၆-၀၉-၂၆: derived ရေးသူ ၄၈ ခုထဲ ၄၄ မှာ ဗလာ-guard မရှိ · ၄၅ မှာ atomic
#    မရှိ ⇒ `gfx_size_16x9.json` (၅၉၃ entry) ဗလာနဲ့ လွှမ်းခံရသည်。
# ⚠️ path ကို **ကိုယ်တိုင် ထည့်ရမည်** — ဒီ script တွေမှာ `core` path insert က
#    `HERE` ရဲ့ အောက်မှာ ရှိသဖြင့် အပေါ်မှာ import လျှင် ကျမည် (တိုင်းပြီး တွေ့)。
try:
    _cp = os.path.join(HERE, "core")
    if _cp not in sys.path:
        sys.path.insert(0, _cp)
    import derived_io as _DIO
except ImportError as _die:      # ⚠️ fail-closed — guard မရှိဘဲ မရေးရ
    raise SystemExit("⛔ core/derived_io.py ဖတ်မရ: %s" % _die)

# ⚠️ S-b — ဂိတ်/တိုင်းချက်က **ဟောင်းနေတဲ့ derived ဖိုင်ကနေ ကိန်း မထုတ်ရ**။
#    ၂၀၂၆-၀၉-၂၅ မှာ ဒီစစ်ချက် မရှိလို့ ၉.၇ နာရီ ဟောင်းတဲ့ `gfx_verify.json`
#    ကနေ 「၆၁၆/၆၁၆ အောင်」 ဟု တင်ပြခဲ့သည်。
try:
    sys.path.insert(0, os.path.join(HERE, "tools"))
    import derived_check as _DC
except Exception:
    _DC = None
sys.path.insert(0, os.path.join(HERE, "core"))
TIMEOUT = 60
# ⚠️ **`dict` ကို နောက်ဆုံး ထားရမည်**။ 2-key dict ကို `(a, b)` အဖြစ် ဖြေလျှင်
#    key နာမည် ရပြီး **အမှား မတက်** ⇒ learner က မှားအောင်ဟု မှတ်သည်
#    (၉ ခုလုံး ဤအတိုင်း · ၂၀၂၆-၀၉-၂၅)。 `pair2` = (စာသား, စာသား)。
ORDER = ("pair", "pair2", "text", "trip", "num", "dict")

CHILD = r'''
import os, sys, json
sys.path.insert(0, os.path.join(%(HERE)r, "core"))
import gfxcat as G, dress as DR
from PIL import Image
eid, sh = sys.argv[1], sys.argv[2]
e = [x for x in G.catalog() if x["id"] == eid][0]
args = G.fill(e, "ဂျပန်မှာ အလုပ်", "ZAE", 62, shape=sh)
if not args: print("0 fill"); raise SystemExit
if DR._wants_tag(e["fn"]): args = ("g0",) + tuple(args)
el = G.call(e, args, 2.0)
fr = (el or {}).get("anim") or (el or {}).get("frames") or []
if len(fr) < 2: print("0 frames"); raise SystemExit
def rp(q): return q if os.path.isabs(q) else os.path.join(G.MK, q)
for it in fr:
    q = rp(it[0] if isinstance(it,(list,tuple)) else it)
    if not os.path.exists(q): print("0 file"); raise SystemExit
last = fr[-1]
im = Image.open(rp(last[0] if isinstance(last,(list,tuple)) else last)).convert("RGBA")
a = im.split()[3]
ink = sum(1 for v in a.getdata() if v > 16) / float(im.width*im.height)
print(("1 " if ink >= 0.0005 else "0 ") + ("ink %%.4f" %% ink))
''' % {"HERE": HERE}


def main():
    import gfxcat as G
    pool = set(l.strip() for l in open(os.path.join(HERE, "assets", "gfx_ok.txt"))
               if l.strip() and not l.startswith("#"))
    # ⚠️ **စာရင်း param ရှိသူများကိုသာ** စစ်ရမည် — ပုံစံ မလိုသူတွေကို
    #    ပုံစံ ၅ မျိုးစီ render လုပ်တာ အချိန်ကုန်ရုံသာ (၄၈၃ ခု × ၅ = ၂၄၁၅ render)。
    # ⚠️ `type == "list"` တစ်ခုတည်းနဲ့ မလုံလောက် — `pairs` · `pins` · `logos`
    #    တွေက catalog မှာ **`text`** ဖြစ်ပြီး စာရင်း ဖြစ်သည် ⇒ ပုံစံ
    #    မသင်ဖြစ်ဘဲ ကျန်ခဲ့သည်。 `gfxcat.fill()` ရဲ့ LISTY နဲ့ တူခဲ့ရမည်。
    LISTY = ("msgs", "results", "tabs", "levels", "stages", "rows", "items",
             "lines", "bullets", "steps", "points", "cols", "labels", "values",
             "data", "pairs", "pins", "fields", "words", "grid", "pts", "cells",
             "parts", "series", "stats", "names", "vals", "kids", "feats",
             "bars", "caps", "segments", "slices")

    def _listy(e):
        for p in (e.get("params") or []):
            if p.get("type") == "list": return True
            if p.get("type") == "text" and p.get("name") in LISTY: return True
        return False

    # ⚠️ **မော်ဒ် ၃ မျိုး** — `derived_check --stale-list` နဲ့ တွဲသုံးရန်。
    #    ပုံမှန်က 「gfx_ok ထဲ မပါသူ」 — gfx_ok မှာ ၁၆၁၆ လုံး ပါသွားသဖြင့်
    #    「၀ ခု」 ပြန်ပြီး ပြန်လေ့လာရန် မရတော့。
    _only = [x for x in (os.environ.get("GFX_ONLY") or "").split(",") if x]
    if _only:
        _os = set(_only)
        todo = [e for e in G.catalog() if e["id"] in _os and _listy(e)]
        print("  (GFX_ONLY — စာရင်း param ရှိသူ %d ခု)" % len(todo), flush=True)
    elif os.environ.get("GFX_RELEARN"):
        todo = [e for e in G.catalog() if _listy(e)]
        print("  (GFX_RELEARN — စာရင်း param ရှိသူ အားလုံး %d ခု)" % len(todo), flush=True)
    else:
        todo = [e for e in G.usable() if e["id"] not in pool and _listy(e)]
    print(f"စစ်မည် {len(todo)} ခု × ပုံစံ {len(ORDER)} မျိုး", flush=True)
    found, won = {}, 0
    for i, e in enumerate(todo, 1):
        hit = None
        for sh in ORDER:
            try:
                p = subprocess.run([sys.executable, "-c", CHILD, e["id"], sh],
                                   capture_output=True, text=True, timeout=TIMEOUT)
                if (p.stdout or "").strip().startswith("1"): hit = sh; break
            except Exception:
                pass
        if hit: found[e["id"]] = hit; won += 1
        print(f"  [{i:3d}/{len(todo)}] {'✓ '+hit if hit else '✖'}  {e['id']}", flush=True)
    # ⚠️ **လွှမ်း၍ မရ** — ဒီပြေးချက်က စာရင်း param ရှိသူတွေကိုသာ ထိသည်;
    #    လွှမ်းလျှင် ရှိပြီးသား ပုံစံတွေ ပျောက်ပြီး template တွေ ပြန်ကျမည်
    #    (`gfx_verify.py` မှာ အတိအကျ ဒီအမှား ဖြစ်ခဲ့ပြီးသား)。
    _p = os.path.join(HERE, "assets", "gfx_args.json")
    try:
        old = json.load(open(_p, encoding="utf-8")) or {}
    except Exception:
        old = {}
    old.update(found)
    print(f"  (ရှိပြီးသား {len(old)-len(found)} နဲ့ ပေါင်း ⇒ {len(old)})", flush=True)
    _DIO.write_derived(_p, old, writer=__file__)
    print(f"\nအလုပ်ဖြစ် {won}/{len(todo)}", flush=True)
    if _DC is not None:
        try:
            _DC.record("gfx_args", ids=[e["id"] for e in todo])
        except Exception as _pe:
            print("  ⚠️ provenance မမှတ်နိုင်: %s" % _pe, flush=True)
    import collections
    print("ပုံစံအလိုက်:", dict(collections.Counter(found.values())))


if __name__ == "__main__":
    main()
