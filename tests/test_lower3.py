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

    print("\n── ၂-ခ · planner ထုတ်သော cid တိုင်း manifest ထဲ ရှိရမည် ──")
    # ⚠️⚠️ ဤစစ်ချက်က ၂၀၂၆-၀၉-၂၈ ရဲ့ ချို့ယွင်းချက်ကို ဖမ်းဖို့ —
    #    route ရဲ့ ဂိတ်ကို `MF.ids()` နဲ့ စစ်ခဲ့ရာ `ids()` (motionkit ဖိုင်
    #    ကနေ · 617) နဲ့ `entry()` (catalog ကနေ · None) **ကွဲ**နေသဖြင့်
    #    `manifest.check()` က「template မရှိ」⇒ **plan တစ်ခုလုံး ပယ်** ⇒
    #    fallback ⇒ **ဂရပ်ဖစ် သုည**。 ဝါကျ တစ်ကြောင်းက ဗီဒီယိုတစ်ခုလုံးရဲ့
    #    ဂရပ်ဖစ်ကို ဖျက်သည် — တိတ်တဆိတ်。
    # ⇒ 「route က မပွင့်သေး」 လို့ စစ်တာ မလုံလောက်。 planner ထုတ်သော
    #   **cid တိုင်း** manifest ထဲ ရှိကြောင်း စစ်ရမည် (ရင်းမြစ် တစ်ခုတည်း)。
    try:
        import manifest as MF
        segs = [dict(text=t, start=i * 3.0, end=i * 3.0 + 2.6, o0=i * 3.0,
                     o1=i * 3.0 + 2.6)
                for i, t in enumerate(
                    ["ဒီနေ့ ပြောမှာက အရေးကြီးတဲ့ အချက် ၃ ချက် ပါ",
                     "နံပါတ် ၁ - ဘာသာစကား အရင် လေ့လာပါ",
                     "ဂျပန်မှာ အလုပ်လုပ်ဖို့ N4 လောက် လိုပါတယ်",
                     "နံပါတ် ၂ - အေဂျင်စီကောင်း ရွေးပါ",
                     "စာရွက်စာတမ်း အကုန် ကြိုပြင်ထားရပါမယ်",
                     "နံပါတ် ၃ - N5 အောင်လက်မှတ် ယူထားပါ"])]
        pl, _ = P.plan(segs, 60.0,
                       {"motionkit_profile": "premium", "aspect": "16:9",
                        "fps": 30}, "j_lt_test", log=lambda m: None)
        evs = [e for e in (pl.get("templateEvents") or [])
               if e.get("motionKitTemplateId")]
        ev = [e["motionKitTemplateId"] for e in evs]
        # ⚠️ `entry()` နဲ့ မစစ်ရ — `headtop.*` က **pack** template ဖြစ်ပြီး
        #    catalog ထဲ မရှိပါ (ကိုယ်ပိုင် manifest ရှိသည်) ⇒ `entry()` က
        #    None ပြန်ကာ မှားပြမည်。 `check()` က တကယ့် စစ်သူ ⇒ **အဲဒါနဲ့ပဲ**
        #    စစ်ရမည် (ဒါက ချို့ယွင်းချက်ရဲ့ သင်ခန်းစာ အတိအကျ — ဂိတ်ကို
        #    စစ်သူနဲ့ တူညီသော ရင်းမြစ် ကနေ ယူရမည်)。
        miss = [(e["motionKitTemplateId"], MF.props_ok(
            e["motionKitTemplateId"], e.get("props") or {})[1])
            for e in evs
            if not MF.props_ok(e["motionKitTemplateId"], e.get("props") or {})[0]]
        check("cid တိုင်း manifest.props_ok() အောင်", not miss, miss)
        # ⚠️ ဂရပ်ဖစ် **သုည မဖြစ်ရ** — ချို့ယွင်းချက်ရဲ့ လက္ခဏာက ဒါ
        check("ဂရပ်ဖစ် သုည မဖြစ်", len(ev) > 0, len(ev))
        # ⚠️ route က ပွင့်ပြီးလျှင် နံပါတ်တပ် ၃ ကြောင်းက **တစ်မျိုးတည်း**
        if MF.entry(P.NUM_LT):
            n_lt = sum(1 for c in ev if c == P.NUM_LT)
            check("နံပါတ်တပ် ၃ ကြောင်း ⇒ lower3 ၃ ခု", n_lt == 3, n_lt)
        else:
            print("  ⊘ lower3 catalog မှာ မမှတ်ရသေး — route စစ်ချက် ကျော်")
    except ImportError as _e:
        print(f"  ⊘ manifest မရ ({_e}) — ဤအပိုင်း ကျော်သည်")

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
