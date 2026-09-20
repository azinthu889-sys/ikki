"""planner — အညွှန်း → timeline တည်ဆောက်ခြင်း test

⚠️ Gemini **မခေါ်ပါ** — quota ကုန်စေပြီး test က ကွန်ရက်ပေါ် မှီခိုသွားမည်。
   `build()` · `fallback()` · `_heuristic()` ကိုသာ စမ်းသည်。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import manifest as MF        # noqa: E402
import plan_schema as PS     # noqa: E402
import planner as PL         # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def seg(a, b, t):
    return dict(start=a, end=b, text=t)


# ၇၈ စက္ကန့် · ဝါကျ ၁၈ ကြောင်း — အမျိုးအစား အစုံ
SEGS = [
    seg(0.0, 3.0, "ဂျပန်မှာ အလုပ်လုပ်ချင်တယ် ဆိုတာ မှန်လား"),
    seg(3.2, 7.0, "Language school နှစ်နှစ်တက်ပြီးတော့ ကုန်ကျစရိတ်တွေ တောင်လိုပုံနေမှာ"),
    seg(7.2, 11.0, "အမှန်တော့ အချိန်နဲ့ငွေကို သက်သာစေမယ့် လမ်းကြောင်းတစ်ခု ရှိပါတယ်"),
    seg(11.2, 15.0, "တစ်နှစ်ပဲ Language school တက်ပြီး Tokutei နဲ့ တိုက်ရိုက် ဝင်တဲ့နည်းပါ"),
    seg(15.2, 19.0, "ကျောင်းနှစ်နှစ်တက်ရတဲ့ program တွေလည်း ရှိပေမဲ့"),
    seg(19.2, 22.0, "Tokutei အတွက် လိုအပ်တဲ့ skill တွေကိုပါ ပြင်ဆင်ပြီး"),
    seg(22.2, 25.0, "အလုပ်တန်းဝင်တဲ့ နည်းလမ်းပါ"),
    seg(25.2, 29.0, "ပထမ အဆင့်ကတော့ N4 အဆင့် ရောက်အောင် လုပ်ရပါမယ်"),
    seg(29.2, 33.0, "ဒါပေမဲ့ ဒီတိုင်းတော့ သွားလို့မရပါဘူး"),
    seg(33.2, 37.0, "လိုအပ်တဲ့ စာရွက်စာတမ်းတွေ ရှိရမယ်"),
    seg(37.2, 41.0, "ကျောင်းက မန္တလေးမြို့မှာ ရှိပါတယ်"),
    seg(41.2, 45.0, "သတိထားရမှာက အေဂျင်စီ အတုတွေ ရှိပါတယ်"),
    seg(45.2, 49.0, "၉၅ ရာခိုင်နှုန်း အောင်မြင်မှု ရှိပါတယ်"),
    seg(49.2, 53.0, "ဒီလိုဆိုရင် ဘာလုပ်ရမလဲ"),
    seg(53.2, 57.0, "ဒုတိယ အဆင့်ကတော့ interview ပြင်ဆင်ခြင်းပါ"),
    seg(57.2, 61.0, "နောက်ဆုံးအနေနဲ့ ပြောချင်တာက"),
    seg(61.2, 68.0, "စောစောစီးစီး ပြင်ဆင်ဖို့ လိုပါတယ်"),
    seg(68.2, 77.0, "အချိန်က မစောင့်ပေးပါဘူး"),
]
DUR = 77.6


def main():
    print("── ၁ · fallback (AI မပါ) ──")
    fb = PL.fallback(SEGS, DUR, video_id="v1")
    ok, e, w = PS.validate(fb, MF, duration=DUR)
    check("fallback က schema အောင်သည်", ok, e[:2])
    check("fallback မှာ စာတန်း ပြည့်သည်", len(fb["captions"]) == len(SEGS))
    check("fallback မှာ ဂရပ်ဖစ် မပါ", not fb["templateEvents"])

    print("\n── ၂ · heuristic အညွှန်း ──")
    labs = PL._heuristic(SEGS)
    check("အညွှန်း အရေအတွက် ကိုက်သည်", len(labs) == len(SEGS))
    check("အညွှန်း အားလုံး ခွင့်ပြုစာရင်းထဲ",
          all(x in PL.LABELS for x in labs), set(labs) - set(PL.LABELS))
    nums = [i for i, x in enumerate(labs) if x == "number"]
    check("number က ဂဏန်းပါသော ဝါကျမှာသာ",
          all(PL._has_digit(SEGS[i]["text"]) for i in nums),
          [SEGS[i]["text"][:20] for i in nums])
    check("ပထမဝါကျက hook", labs[0] == "hook")

    print("\n── ၃ · build (standard) ──")
    p = PL.build(SEGS, labs, DUR, dict(energy="standard"), "v1")
    ok, e, w = PS.validate(p, MF, duration=DUR)
    check("standard plan က schema အောင်သည်", ok, e[:3])
    check("စာတန်းက စကားတိုင်းမှာ ရှိသည်", len(p["captions"]) == len(SEGS))

    tids = [x["motionKitTemplateId"] for x in p["templateEvents"]]
    check("template ID အားလုံး တကယ်ရှိသည်",
          all(c in MF.ids() for c in tids), [c for c in tids if c not in MF.ids()])
    check("ဆက်တိုက် တူသော template မရှိ",
          all(a != b for a, b in zip(tids, tids[1:])), tids)

    ts = [x["startTime"] for x in p["templateEvents"]]
    gaps = [b - a for a, b in zip(ts, ts[1:])]
    check("ကြားကာလ ပစ်မှတ် ထိန်းသည်",
          all(g >= PL.ENERGY["standard"]["gap"] - 0.01 for g in gaps),
          [round(g, 1) for g in gaps])

    pun = p["cameraReframes"]
    check("punch ၁.၀၈ မကျော်",
          all(x["props"]["zoom"] <= PS.MAX_PUNCH for x in pun))
    check("punch သတိပေးချက် မရှိ",
          not any(x["code"].startswith("punch") for x in w), w)

    print("\n── ၄ · စွမ်းအင် အဆင့် ၃ မျိုး ──")
    counts = {}
    for lvl in ("minimal", "standard", "dynamic"):
        q = PL.build(SEGS, labs, DUR, dict(energy=lvl), "v1")
        ok2, e2, _ = PS.validate(q, MF, duration=DUR)
        counts[lvl] = len(q["templateEvents"])
        check(f"{lvl} က schema အောင်သည်", ok2, e2[:2])
    print(f"    ဂရပ်ဖစ် — minimal {counts['minimal']} · "
          f"standard {counts['standard']} · dynamic {counts['dynamic']}")
    check("dynamic ≥ standard ≥ minimal",
          counts["dynamic"] >= counts["standard"] >= counts["minimal"], counts)
    check("minimal မှာ punch မပါ",
          not PL.build(SEGS, labs, DUR, dict(energy="minimal"), "v1")["cameraReframes"])

    print("\n── ၅ · အရောင် စည်းမျဉ်း ──")
    # ⚠️ အရောင်က `style` ထဲ ရှိသည် — `props` က template ရဲ့ argument သာ
    cols = [c["style"]["color"] for c in p["captions"]]
    check("အရောင် ၃ မျိုးသာ", set(cols) <= PS.CAPTION_COLORS, set(cols))
    nwhite = sum(1 for c in cols if c != PS.WHITE)
    check("အလေးထားမှု အနည်းငယ်သာ (၄၀% အောက်)",
          nwhite <= len(cols) * 0.4, f"{nwhite}/{len(cols)}")

    print("\n── ၅ခ · မြန်မာ စာကြောင်း ခွဲခြင်း ──")
    long_t = "ကျောင်းနှစ်နှစ်တက်ရတဲ့ program တွေလည်း ရှိပေမဲ့ ဒီရွေးချယ်မှုကတော့ ပိုမြန်ပါတယ်"
    two = PL.split2(long_t)
    check("၂ ကြောင်းထက် မပိုပါ", len(two) <= 2, two)
    check("စာလုံး တစ်လုံးမှ မပျောက်ပါ",
          "".join(two).replace(" ", "") == long_t.replace(" ", ""))
    nospace = "ကျောင်းနှစ်နှစ်တက်ရတဲ့program"
    check("space မရှိလျှင် မခွဲပါ (glyph မပျက်စေရန်)",
          PL.split2(nospace) == [nospace], PL.split2(nospace))

    print("\n── ၅ဂ · ကတ်စာသား အတိုချုံးခြင်း ──")
    # ⚠️ ၂၀၂၆-၀၉-၂၁ — `t[:26]` က 「…တက်ပြီးတော့」ကို 「…တက်ပြီးတ」ဖြစ်စေခဲ့သည်
    card = "Language school နှစ်နှစ်တက်ပြီးတော့ ကုန်ကျစရိတ်တွေ"
    sh = PL._short(card)
    check("စာလုံး အလယ် မပြတ်ပါ", card.startswith(sh) and
          (len(sh) == len(card) or card[len(sh)] == " "), sh)
    check("cluster နဲ့ တိုင်းသည် (code point မဟုတ်)",
          PL._ncl("ပြီး") == 1, PL._ncl("ပြီး"))
    check("ဘောင် မကျော်ပါ", PL._ncl(sh) <= 26, PL._ncl(sh))
    check("space မရှိလျှင် အပြည့် ပြန်ပေးသည်",
          PL._short("ကျောင်းနှစ်နှစ်တက်ရတဲ့ပရိုဂရမ်တွေကိုလည်းလေ့လာရမယ်") ==
          "ကျောင်းနှစ်နှစ်တက်ရတဲ့ပရိုဂရမ်တွေကိုလည်းလေ့လာရမယ်")

    print("\n── ၆ · AI က အမျိုးအစား တီထွင်လျှင် ──")
    bogus = ["totally_made_up"] * len(SEGS)
    q = PL.build(SEGS, bogus, DUR, dict(energy="standard"), "v1")
    ok3, e3, _ = PS.validate(q, MF, duration=DUR)
    check("မသိသော အညွှန်းနဲ့လည်း schema အောင်သည်", ok3, e3[:2])
    check("မသိသော အညွှန်းက ဂရပ်ဖစ် မထုတ်ပါ", not q["templateEvents"])

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
