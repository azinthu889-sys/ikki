# -*- coding: utf-8 -*-
"""`planner.ALIAS` — နာမည် ကွဲသူကို ချိတ်ခြင်း。

⚠️ ဤစမ်းသပ်ချက်က **ဂိတ် မလျှော့ကြောင်း** စစ်သည် — alias က
   ① ရှိပြီးသား key ကို မဖျက်ရ ② မသေချာသူ ၅၅ ခုကို မချိတ်ရ
   ③ chart ဂိတ်ကို မကျော်ရ (alias ပြီးမှ စစ်ရမည်)
   ④ `IKKI_GFX_ALIAS=0` နဲ့ အဟောင်း ပြန်ရရမည်。
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "core"))

TXT = "Tokutei ဗီဇာလမ်းကြောင်းက ဒီလို ဖြစ်တယ် — N5 အောင်ရမယ်"


def _fillable(flag):
    os.environ["IKKI_GFX_ALIAS"] = flag
    import planner as PL
    importlib.reload(PL)
    out = set()
    for lab in sorted(PL.FAMILY):
        for x in PL._profile_candidates(lab, "premium", None):
            try:
                if PL.fill(x, lab, TXT) is not None:
                    out.add(x)
            except Exception:
                pass
    return out, PL


def main():
    fails = []
    off, PL0 = _fillable("0")
    on, PL = _fillable("1")

    # ① alias က ရှိပြီးသား key ကို မဖျက်ရ
    src = set(PL.ALIAS)
    import manifest as MF
    import gfxcat as G
    known = set()
    for e in G.catalog():
        for p in ((MF.entry(e["id"]) or {}).get("params") or []):
            known.add(p.get("name"))
    # `m` dict ရဲ့ key ကို ALIAS ရဲ့ **source** အဖြစ် မသုံးရ
    mkeys = set(PL.ALIAS.values())
    clash = src & mkeys
    if clash:
        fails.append(f"alias source က ပစ်မှတ် key နဲ့ ထပ်: {sorted(clash)}")

    # ② မသေချာသူ — ပုံ/ပထဝီ ကို ဘယ်တော့မှ မချိတ်ရ
    BAN = {"img", "imgs", "image", "img_path", "img1", "img2", "img_a",
           "img_b", "logo", "logos", "photo", "avatar", "lat", "lon",
           "lat0", "lat1", "lon0", "lon1"}
    bad = BAN & src
    if bad:
        fails.append(f"ပုံ/ပထဝီ param ကို ချိတ်ထား: {sorted(bad)}")

    # ③ chart ဂိတ် — ကိန်းအတွဲ မရှိဘဲ chart မဆွဲရ
    import collections
    chart_bad = []
    for e in G.catalog():
        m = MF.entry(e["id"]) or {}
        if (m.get("category") or "").lower() != "chart":
            continue
        req = {p.get("name") for p in (m.get("params") or [])
               if p.get("required")}
        req = {PL.ALIAS.get(n, n) for n in req}
        if "rows" in req and PL.fill(e["id"], "number", TXT) is not None:
            chart_bad.append(e["id"])
    if chart_bad:
        fails.append(f"chart က ကိန်းအတွဲ မရှိဘဲ ဖြည့်ရ: {chart_bad[:5]}")

    # ④ flag က တကယ် အလုပ်လုပ်ရမည် · alias က **တိုးရ**မည်၊ မလျော့ရ
    if not off < on:
        fails.append(f"alias က superset မဟုတ် (ရှေး {len(off)} · ယခု {len(on)})")
    if len(on) - len(off) < 100:
        fails.append(f"alias ရဲ့ အကျိုး သေးလွန်း: +{len(on)-len(off)} (တိုင်းချက် +125)")

    print(f"  alias {len(PL.ALIAS)} လုံး · fill {len(off)} → {len(on)} "
          f"(+{len(on)-len(off)}) · chart ဖြည့်ရ {0 if not chart_bad else len(chart_bad)}")
    for f in fails:
        print(f"  ✗ {f}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
