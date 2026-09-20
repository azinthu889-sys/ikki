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
sys.path.insert(0, os.path.join(HERE, "core"))
TIMEOUT = 60
ORDER = ("pair", "text", "trip", "dict", "num")

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
    todo = [e for e in G.usable() if e["id"] not in pool]
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
    json.dump(found, open(os.path.join(HERE, "assets", "gfx_args.json"), "w"),
              ensure_ascii=False, indent=1, sort_keys=True)
    print(f"\nအလုပ်ဖြစ် {won}/{len(todo)}", flush=True)
    import collections
    print("ပုံစံအလိုက်:", dict(collections.Counter(found.values())))


if __name__ == "__main__":
    main()
