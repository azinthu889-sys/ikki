# -*- coding: utf-8 -*-
"""ချောင်းဆိုးသံ/ဖြည့်စကား — **အတည်ပြုမှ ဖျက်** (Cut audit P0)

⚠️ Zin ရဲ့ စည်းကမ်း: 「user အတည်ပြုမှဖျက်ပေး။ script editor မှာပဲအနီပြထား」
⚠️ `coughs()` က အမြင့်ဘန်း တက်မှုကိုသာ ရှာသည် — ချောင်းလား · စ/ဆ သံလား ·
   ကီးဘုတ်လား **မခွဲနိုင်ပါ**。 precision မတိုင်းရသေး ⇒ review-first。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))
import clean as CL       # noqa: E402
import recipes as RC     # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def main():
    # ⚠️ detector ကိုယ်တိုင်ကို မစစ်ပါ — **လမ်းကြောင်း** ကို စစ်သည်
    #    (detector က synthetic အသံမှာ မဖမ်းသဖြင့် လမ်းကြောင်း မပေါ်)
    co = [dict(at=1.0, to=1.2, kind="cough", auto=True)]
    fi = [dict(at=3.0, to=3.3, kind="filler", auto=True, text="အဲ့ဒါ")]
    _c, _f = CL.coughs, CL.fillers
    CL.coughs = lambda *a, **k: [dict(x) for x in co]
    CL.fillers = lambda *a, **k: [dict(x) for x in fi]
    try:
        print("── ၁ · ပုံသေ ⇒ ညွှန်ပြရုံ ──")
        au, fl = CL.plan("x.wav", [])
        check("auto ဗလာ", au == [], au)
        kinds = sorted(c.get("kind") for c in fl)
        check("cough+filler က flags ထဲ", "cough" in kinds and "filler" in kinds, kinds)
        check("auto=False အဖြစ် မှတ်ထား",
              all(c.get("auto") is False for c in fl if c.get("kind") in
                  ("cough", "filler")), fl)
        check("အကြောင်းရင်း ပါ",
              all(c.get("note") for c in fl if c.get("kind") in
                  ("cough", "filler")), fl)

        print("\n── ၂ · auto_clean=True ⇒ အလိုအလျောက် ──")
        au2, fl2 = CL.plan("x.wav", [], auto_ok=True)
        check("auto ၂ ခု", len(au2) == 2, au2)
        k2 = sorted(c.get("kind") for c in fl2)
        check("flags ထဲ မပါတော့", "cough" not in k2 and "filler" not in k2, k2)

        print("\n── ၃ · ရှာတာကို မရပ်ရ ──")
        # ⚠️ ညွှန်ပြချက် ဖြစ်သွားလည်း **ရှာတာ ဆက်လုပ်ရမည်** — မရှာလျှင်
        #    editor က အလကား ဖြစ်သည်
        check("ပုံသေမှာလည်း တွေ့သည်", len(fl) >= 2, fl)

        print("\n── ၄ · အချိန်အလိုက် စီထား ──")
        ats = [c.get("at", 0) for c in fl]
        check("flags စီပြီး", ats == sorted(ats), ats)
    finally:
        CL.coughs, CL.fillers = _c, _f

    print("\n── ၅ · recipe အားလုံး ပုံသေ ပိတ် ──")
    bad = []
    for e in RC.listing():
        k = e.get("id") if isinstance(e, dict) else e
        if RC.apply(k, {}).get("auto_clean"):
            bad.append(k)
    check("auto_clean အားလုံး False", not bad, bad)

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
