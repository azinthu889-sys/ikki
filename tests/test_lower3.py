#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lower3 — နံပါတ်တပ် lower third ရဲ့ **ရွေးထုတ်ချက်** နဲ့ ဂျီဩမေတြီ

⚠️ ဤဖိုင်က ၂ ပိုင်း — `numbered_item()` က motionkit မလိုပါ (အမြဲ ပြေးသည်)、
   template ဂျီဩမေတြီက motionkit ရှိမှသာ ပြေးသည် (မရှိလျှင် ကျော်)。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core"))
import planner as P                                        # noqa: E402

FAILED = []


def check(name, ok, got=None):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  · {got!r}"))
    if not ok:
        FAILED.append(name)


def main():
    print("── ၁ · နံပါတ်တပ် item ဟုတ်/မဟုတ် ──")
    # ⚠️ တကယ့် ASR ထွက်ချက် ၃ မျိုးလုံး — 「နံပါတ် ၃」(ဂဏန်း) ·
    #    「နံပါတ်၃။」(space မပါ) · Latin 「2.」 ([[ikki-graphic-variety]])
    yes = [("နံပါတ် ၂ - အေဂျင်စီကောင်း", "02", "အေဂျင်စီကောင်း"),
           ("နံပါတ်၃။ N5 အောင်လက်မှတ်", "03", "N5 အောင်လက်မှတ်"),
           ("2. Good agency", "02", "Good agency"),
           ("#1 ချောမွေ့တဲ့ လမ်းကြောင်း", "01", "ချောမွေ့တဲ့ လမ်းကြောင်း"),
           ("No.2 ကောင်းတဲ့ ကျောင်း", "02", "ကောင်းတဲ့ ကျောင်း"),
           ("(၁) စာမေးပွဲ အောင်ရမယ်", "01", "စာမေးပွဲ အောင်ရမယ်")]
    for t, n, h in yes:
        r = P.numbered_item(t)
        check(f"item ⇒ {n}  「{t}」", r is not None and r[0] == n and r[1] == h, r)
    print("\n── ၂ · item **မဟုတ်**သည်များ ──")
    # ⚠️ ဂဏန်းပါတိုင်း item မဟုတ် — ခုနှစ်သက္ကရာဇ်/အရေအတွက်က အများဆုံး
    #    မှားစရာ ([[ikki-verifier-traps]] ရဲ့ အတန်း — ဂိတ်က ကိုယ်တိုင် မှားခြင်း)
    no = ["၂၀၂၆ မှာ ဂျပန်သွားမယ်", "၅ နှစ် နေခဲ့တယ်", "ဒါက သာမန် ဝါကျ",
          "နံပါတ် ၂ ပါ", "", "   ", "N5 စာမေးပွဲ ဖြေမယ်"]
    for t in no:
        check(f"item မဟုတ်  「{t}」", P.numbered_item(t) is None, P.numbered_item(t))
    # ⚠️ ၂၀ ထက် ကြီးလျှင် item မဟုတ် — badge မှာ ဂဏန်း ၂ လုံးသာ ဆံ့သည်
    check("၂၀ ကျော် ⇒ item မဟုတ်", P.numbered_item("45. တစ်ခုခု ဖြစ်တယ်") is None,
          P.numbered_item("45. တစ်ခုခု ဖြစ်တယ်"))

    print("\n── ၃ · template ဂျီဩမေတြီ (motionkit ရှိမှ) ──")
    try:
        import theme                                        # noqa: F401
        import lower3 as L
    except Exception as e:
        print(f"  ⊘ motionkit မရှိ ({type(e).__name__}) — ဤအပိုင်း ကျော်သည်")
        return 1 if FAILED else 0
    import numpy as np
    from PIL import Image
    for size, cap in (("9:16", 1550 / 1920), ("16:9", 1550 / 1920)):
        theme.use("ikki", size)
        import importlib
        importlib.reload(L)
        from kit import W, H
        e = L.lt_number(f"t{size.replace(':', 'x')}", "02", "အေဂျင်စီကောင်း", dur=3.0)
        a = np.array(Image.open(e["anim"][60][0]).convert("RGBA").split()[3])
        ys, xs = np.where(a > 200)
        # ⚠️ **မင် အောက်စွန်း** ကို စစ်ရမည် — alpha bbox မှာ glow/အရိပ်
        #    ပါသဖြင့် အမြဲ ကျော်နေမည် (ဖရိန် တိုင်းမှ တွေ့ခဲ့သည်)。
        check(f"{size} အောက်စွန်း ≤ စာတန်း ကန့်သတ်", ys.max() <= int(H() * cap) + 1,
              (int(ys.max()), int(H() * cap)))
        check(f"{size} ဘောင်အတွင်း", xs.min() >= 0 and xs.max() < W(),
              (int(xs.min()), int(xs.max()), W()))
        check(f"{size} ဘောင်အပြည့် မဟုတ်", (ys.max() - ys.min()) < H() * 0.25,
              int(ys.max() - ys.min()))
        check(f"{size} sfx ကြေညာချက် ရှိ", len(e["sfx"]) >= 2, e["sfx"])
    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    sys.exit(main())
