# -*- coding: utf-8 -*-
"""ဂရပ်ဖစ် အမြင့် ↔ ရနိုင်သော နေရာ (Overlay audit P0)

⚠️ တကယ့် headtop render မှာ ဂရပ်ဖစ် ၇ ခု ရွေးပြီး **၀–၃ ခုသာ** တပ်ဖြစ်ခဲ့သည် —
   မျက်နှာဇုန် ၀–၆၉၆ နဲ့ စာတန်းထိပ် ၇၅၇ ကြားမှာ **၆၁ px သာ** ကျန်၍。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))
import dress as D    # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def main():
    H = 1080
    print("── ၁ · နေရာ တွက်ချက် ──")
    # တကယ့် render ရဲ့ ကိန်းများ — မျက်နှာ ၀–၆၉၆ · စာတန်းထိပ် ၇၅၇
    r = D.room((0, 696), 757, H)
    check("headtop အခြေအနေ ⇒ ၆၁px", r == 757 - 12 - (696 + 16), r)
    check("avoid မရှိ ⇒ ဘောင်အပြည့်", D.room(None, 757, H) == H)
    # မျက်နှာက အောက်ပိုင်းမှာ ⇒ ခေါင်းအထက် နေရာ ရှိ
    r2 = D.room((600, 900), 1000, H)
    check("မျက်နှာ အောက် ⇒ အပေါ်က နေရာ", r2 == 600 - int(H * 0.075) - 8, r2)
    check("နေရာက အနုတ် မဖြစ်ရ", D.room((0, 1070), 1075, H) >= 0)

    print("\n── ၂ · တိုင်းချက် ဖိုင် ──")
    sz = D.sizes("16:9")
    # ⚠️ တိုင်းချက် **အရေအတွက်** က သီးခြား ဂိတ် — ဒီ test က ယုတ္တိကို စစ်သည်。
    #    ကိန်း မပြည့်စုံလျှင် ရှင်းရှင်း ပြောပြီး လဲလှယ်မှု စစ်ချက်ကို ကျော်သည်
    #    (「မပြေးဘဲ အောင်」 မဖြစ်စေရန် — ကျော်ကြောင်း အတိအလင်း ပြသည်)。
    bad = [k for k, v in sz.items() if not isinstance(v.get("h"), int) or v["h"] < 0]
    check("အမြင့် အားလုံး မှန်", not bad, bad[:3])
    check("တိုင်းချက် မရှိလျှင်လည်း မပျက်ရ",
          D.fits("__none__", (0, 696), 757, H))
    ENOUGH = len(sz) >= 50
    print(f"    တိုင်းထားသည် {len(sz)} ခု"
          + ("" if ENOUGH else " — ၅၀ အောက် ⇒ လဲလှယ်မှု စစ်ချက် ကျော်သည် "
                              "(`python3 tools/gfxsize.py --fmt=16:9` ပြေးရန်)"))

    print("\n── ၃ · မသိသော template ကို ကြိုမပယ်ရ ──")
    # ⚠️ တိုင်းချက် မရှိလျှင် **ခွင့်ပြု**ရမည် — ပယ်လျှင် template အသစ်
    #    တိုင်း တိတ်တဆိတ် ပျောက်မည်
    check("မသိ ⇒ ခွင့်ပြု", D.fits("__no_such_template__", (0, 696), 757, H))

    print("\n── ၄ · လဲလှယ်မှု ──")
    gfx = [dict(at=2.0, kind="box_call"), dict(at=9.0, kind="box_call")]
    out, n = D.swap_fit(gfx, (0, 696), 757, H, seed="j1", fmt="16:9")
    check("ရေတွက် မပြောင်း", len(out) == len(gfx), (len(out), len(gfx)))
    if ENOUGH and "box_call" in sz and sz["box_call"]["h"] > D.room((0, 696), 757, H):
        check("မဝင်သော template လဲပြီး", n > 0, n)
        bad = [g["kind"] for g in out
               if not D.fits(g["kind"], (0, 696), 757, H, "16:9")]
        check("လဲပြီးတာ အားလုံး ဝင်ဆံ့", not bad, bad)
        # ⚠️ headtop framing မှာ ကျန်နေရာက **၃၃px** သာ ဖြစ်ပြီး တိုင်းထားသော
        #    template ၂၄၃ ခုထဲက တစ်ခုမှ မဝင်ပါ ⇒ အစားထိုးက **ပြောသူပေါ်
        #    တင်နိုင်သော pack template** ဖြစ်မည် (အတူတူ ဖြစ်နိုင်သည်)。
        if D.room((0, 696), 757, H) >= 61:
            check("အတူတူ မထပ်", len({g["kind"] for g in out}) == len(out),
                  [g["kind"] for g in out])
        else:
            check("ပြောသူပေါ် တင်နိုင်သော အစားထိုး သုံးသည်",
                  all(D._over_subject(g["kind"]) for g in out),
                  [g["kind"] for g in out])
    # ⚠️ တူညီသော seed ⇒ တူညီသော အစားထိုး (ပြန်ထုတ်လျှင် တူရန်)
    o2, _ = D.swap_fit(gfx, (0, 696), 757, H, seed="j1", fmt="16:9")
    check("seed တူ ⇒ ရလဒ် တူ",
          [g["kind"] for g in out] == [g["kind"] for g in o2])

    print("\n── ၅ · နေရာ ကျယ်လျှင် မလဲရ ──")
    out3, n3 = D.swap_fit(gfx, None, 1080, H, seed="j1", fmt="16:9")
    check("မလဲပါ", n3 == 0 and [g["kind"] for g in out3] == ["box_call"] * 2,
          (n3, [g["kind"] for g in out3]))

    print("\n── ၅b · ပြောသူပေါ် တင်နိုင်သော template ──")
    subp = D._subject_pool()
    check("pack မှာ ရှိသည်", len(subp) >= 1, subp)
    for t in subp:
        check(f"{t} က အမြင့်နဲ့ မပယ်ခံရ", D.fits(t, (0, 696), 757, H), t)

    print("\n── ၆ · `room()` က placement နဲ့ တစ်ထပ်တည်း ──")
    # ⚠️ တွက်နည်း ၂ ခု ကွဲသွားလျှင် ကြိုစစ်ချက် အလကား ဖြစ်သည်
    for avoid, capy in (((0, 696), 757), ((0, 500), 900), ((300, 800), 1000)):
        ay0, ay1 = avoid
        TOP = int(H * 0.075)
        above = ay0 - TOP - 8
        below = (capy - 12) - (ay1 + 16)
        check(f"avoid={avoid} capy={capy}",
              D.room(avoid, capy, H) == max(0, above, below),
              (D.room(avoid, capy, H), above, below))

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
