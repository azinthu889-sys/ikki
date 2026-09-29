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
           ("(၁) စာမေးပွဲ အောင်ရမယ်", "01", "စာမေးပွဲ အောင်ရမယ်"),
           # ⚠️ ASR က ဂဏန်းကို **စာလုံးနဲ့** ရေးတတ်သည် — ဒါက တကယ့် ဒေတာ
           #    (၂၀၂၆-၀၉-၂၉ short-916 final4)。 ဒီပုံစံ မဖမ်းမိလို့
           #    lower3 က **၀ ကြိမ်** သုံးဖြစ်ခဲ့သည်。
           ("နံပါတ်တစ် COE စိတ်ချရတဲ့ Class 1 ကျောင်း", "01",
            "COE စိတ်ချရတဲ့ Class 1 ကျောင်း"),
           ("နံပါတ်နှစ် ဂျပန်ရောက်တဲ့အထိ", "02", "ဂျပန်ရောက်တဲ့အထိ"),
           ("နံပါတ်သုံး ကိုယ့်ဘက်က အထက်တန်း", "03", "ကိုယ့်ဘက်က အထက်တန်း")]
    for t, n, h in yes:
        r = P.numbered_item(t)
        check(f"item ⇒ {n}  「{t}」", r is not None and r[0] == n and r[1] == h, r)
    print("\n── ၂ · item **မဟုတ်**သည်များ ──")
    # ⚠️ ဂဏန်းပါတိုင်း item မဟုတ် — ခုနှစ်သက္ကရာဇ်/အရေအတွက်က အများဆုံး
    #    မှားစရာ ([[ikki-verifier-traps]] ရဲ့ အတန်း — ဂိတ်က ကိုယ်တိုင် မှားခြင်း)
    no = ["၂၀၂၆ မှာ ဂျပန်သွားမယ်", "၅ နှစ် နေခဲ့တယ်", "ဒါက သာမန် ဝါကျ",
          "နံပါတ် ၂ ပါ", "", "   ", "N5 စာမေးပွဲ ဖြေမယ်",
          # ⚠️ စာလုံး ဂဏန်းကို **ရှေ့ဆက် မပါဘဲ** လက်မခံရ —「နှစ်」က
          #    「year」လည် ဖြစ်နိုင်သည်。「နံပါတ်」 ရဲ့ နောက်မှာမှသာ မဖြစ်နိုင်。
          "နှစ်နှစ် နေခဲ့တယ်", "သုံးလ ကြာတယ်", "လေးယောက် ရှိတယ်",
          # ⚠️ ခေါင်းစဉ် မရှိလျှင် ကတ် မထုတ်ရ
          "နံပါတ်နှစ်"]
    for t in no:
        check(f"item မဟုတ်  「{t}」", P.numbered_item(t) is None, P.numbered_item(t))
    # ⚠️ ၂၀ ထက် ကြီးလျှင် item မဟုတ် — badge မှာ ဂဏန်း ၂ လုံးသာ ဆံ့သည်
    check("၂၀ ကျော် ⇒ item မဟုတ်", P.numbered_item("45. တစ်ခုခု ဖြစ်တယ်") is None,
          P.numbered_item("45. တစ်ခုခု ဖြစ်တယ်"))

    print("\n── ၂-ဃ · နေရာ ကတ်က **နေရာ နာမည်** ပြရမည် ──")
    # ⚠️ ၂၀၂၆-၀၉-၂၉ — `place` ကို `_short(text, 20)` နဲ့ ဖြည့်ခဲ့ရာ ဝါကျရဲ့
    #    ရှေ့ စကားလုံးများ တင်မိသည်:「ကျောင်းရဲ့ ဒီနေရာကလည်း」。 တကယ့် နေရာ
    #    「Takadanobaba」က **အဲဒီ ဝါကျထဲမှာပဲ** ရှိပြီး B-roll matcher က
    #    တွေ့ပြီးသား — ကတ်ကပဲ မရှာခြင်း。
    for _t, _w in (("ကျောင်းရဲ့ ဒီနေရာကလည်း Takadanobaba မှာ ရှိပါတယ်",
                    "Takadanobaba"),
                   ("Tokyo နဲ့ Osaka ၂ ခု", "Tokyo"),
                   ("Shinjuku station အနား", "Shinjuku")):
        check(f"နေရာ ⇒ {_w}", P.place_of(_t) == _w, P.place_of(_t))
    # ⚠️ **ခန့်မှန်း၍ မဖြည့်ရ** — အစီအစဉ်/အဖွဲ့အစည်း နာမည်က နေရာ မဟုတ်
    for _t in ("ဒါက သာမန် ဝါကျ ဖြစ်ပါတယ်",
               "Japanese Language School မှာ တက်ခဲ့တယ်",
               "Tokutei skill program နဲ့ သွားမယ်",
               "N5 level အောင်ရမယ်", ""):
        check(f"နေရာ မဟုတ် ⇒ None  「{_t[:18]}」", P.place_of(_t) is None,
              P.place_of(_t))

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
        # ⚠️ ဝါကျ ခြားချိန်ကို **တကယ့် ဒေတာနဲ့ တူအောင်** ထားရမည် —
        #    ၃ စက္ကန့်ခြားလျှင် ကတ် အကွာအဝေး စည်းမျဉ်း မိပြီး 「၃ ခုထဲ ၁ ခု」
        #    သာ ရကာ **စမ်းသပ်ချက်က တကယ်မဟုတ်သော ကန့်သတ်ချက်** ကို
        #    တိုင်းနေမည် (၂၀၂၆-၀၉-၂၉)。 short-916 ရဲ့ item တွေက
        #    ~၁၂ စက္ကန့် ခြားသည်。
        segs = [dict(text=t, start=i * 12.0, end=i * 12.0 + 4.0, o0=i * 12.0,
                     o1=i * 12.0 + 4.0)
                for i, t in enumerate(
                    ["ဒီနေ့ ပြောမှာက အရေးကြီးတဲ့ အချက် ၃ ချက် ပါ",
                     "နံပါတ် ၁ - ဘာသာစကား အရင် လေ့လာပါ",
                     "ဂျပန်မှာ အလုပ်လုပ်ဖို့ N4 လောက် လိုပါတယ်",
                     "နံပါတ် ၂ - အေဂျင်စီကောင်း ရွေးပါ",
                     "စာရွက်စာတမ်း အကုန် ကြိုပြင်ထားရပါမယ်",
                     "နံပါတ် ၃ - N5 အောင်လက်မှတ် ယူထားပါ"])]
        pl, _ = P.plan(segs, 80.0,
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

    print("\n── ၂-ဂ · ခေါင်းစဉ် ကျော်လျှင် **ဖြတ်**ရမည် (၉:၁၆ ရော ၁၆:၉ ရော) ──")
    # ⚠️⚠️ **ဖွဲ့စည်းထားသော ဖရိန်ကနေ တိုင်းလို့ မရ**。 နောက်ဆုံး ဆွဲသည့်
    #    canvas က `tw` အကျယ်သာ ဖြစ်ပြီး cttext က အဲဒီမှာ **ဖြတ်**သဖြင့်
    #    မင်က `tw` ကို ဘယ်တော့မှ မကျော်နိုင် ⇒ 「ဆံ့သည်」 ဟု **အမြဲ** ✓
    #    ပြမည် (၂၀၂၆-၀၉-၂၉ — ငါ့ ပထမ စမ်းသပ်ချက် အဲဒီလို လိမ်ခဲ့သည်)。
    #    ⇒ **ကျယ်သော canvas** ထဲ ဆွဲပြီး တိုင်းမှသာ အမှန် ရသည်。
    try:
        import theme as _th
        import lower3 as _L3
        import importlib as _il
        from prem import txt as _txt
        from kit import W as _W, H as _H
        from PIL import Image as _Im
        _n = [0]
        for _asp in ("9:16", "16:9"):
            _th.use("ikki", _asp)
            _il.reload(_L3)
            _w, _h = _W(), _H()
            _side = _w * _L3.R_SIDE
            _bs = _h * _L3.R_BS
            _px0 = _side + _bs - _w * (40 / 1080)
            _tx = _px0 + _w * (72 / 1080)
            _tw = (_w - _side) - _tx - _w * (36 / 1080)
            _pw = int(_tw * 3)

            def _wide(_t, _sz):
                # ⚠️ tag ကို **တိုင်းတိုင်း အသစ်** — တူလျှင် ရှေ့က ဖိုင် ပြန်ရပြီး
                #    အကျယ် မပြောင်း (token loop က တစ်လုံးအထိ ဖြတ်မိသည်)
                _n[0] += 1
                _p = _txt(f"tw{_n[0]}", _t, _sz, "#FFFFFF", None, _pw)
                _b = _Im.open(_p).split()[3].getbbox()
                return _b[2] - _b[0]

            for _t in ("COE စိတ်ချရတဲ့ Class 1 ကျောင်းဖြစ်ဖို့ အရေးကြီးပါတယ်",
                       "ကိုယ့်ဘက်က အထက်တန်းအောင်မြင်ထားဖို့ လိုပါတယ်",
                       "အေဂျင်စီကောင်း"):
                _hs = int(_h * _L3.R_HEAD_MAX)
                _hmin = int(_h * _L3.R_HEAD_MIN)
                while _hs > _hmin and _wide(_t, _hs) > _tw:
                    _hs -= 2
                _tk = _t.split()
                _d = 0
                while len(_tk) - _d > 1 and \
                        _wide(" ".join(_tk[:len(_tk) - _d]), _hs) > _tw:
                    _d += 1
                _fin = " ".join(_tk[:len(_tk) - _d])
                _wd = _wide(_fin, _hs)
                check(f"{_asp} ဖြတ်ပြီး ဆံ့  「{_t[:14]}…」",
                      _wd <= _tw, (int(_wd), int(_tw)))
                # ⚠️ **အကုန် မဖြတ်ပစ်ရ** — tag ထပ်မိလျှင် တစ်လုံးအထိ ဖြတ်သည်
                check(f"{_asp} token အကုန် မဖြတ်  「{_t[:14]}…」",
                      _wd > _tw * 0.25, (int(_wd), int(_tw)))
        _th.use("ikki", "9:16")
        _il.reload(_L3)
    except ImportError as _e:
        print(f"  ⊘ motionkit မရ ({_e}) — ဤအပိုင်း ကျော်သည်")

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
