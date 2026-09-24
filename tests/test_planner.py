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
    screen_labs = PL._heuristic([
        seg(0, 3, "ဒီနေ့ အရေးကြီးတဲ့အချက်ကို ပြမယ်"),
        seg(3.2, 6.0, "IKKI app dashboard screen ကိုပြမယ်"),
    ])
    check("app / screen ကို UI label ခွဲသည်", screen_labs[1] == "screen", screen_labs)

    print("\n── ၃ · build (standard) ──")
    p = PL.build(SEGS, labs, DUR, dict(energy="standard"), "v1")
    ok, e, w = PS.validate(p, MF, duration=DUR)
    check("standard plan က schema အောင်သည်", ok, e[:3])
    check("စာတန်းက စကားတိုင်းမှာ ရှိသည်", len(p["captions"]) == len(SEGS))

    # ⚠️ `templateEvents` ထဲ **မိသားစု ၂ ခု** ရှိသည် —
    #    ① အဓိပ္ပာယ်ဆိုင်ရာ ဂရပ်ဖစ် (ကတ် · ပုံကြမ်း) — ကြားကာလ/မထပ် စည်းမျဉ်း ရှိ
    #    ② keyword pop — တိုင်းထားသော သီးသန့် စည်းချက် (`docs/HEADTALK_STYLE.md`)
    #    ⇒ စည်းမျဉ်းတွေကို **ခွဲစစ်ရမည်**、ရောစစ်လျှင် အဓိပ္ပာယ် မရှိပါ。
    def _pops(q): return [x for x in q["templateEvents"]
                          if (x.get("style") or {}).get("kind") == "pop"]
    def _gfx(q): return [x for x in q["templateEvents"]
                         if (x.get("style") or {}).get("kind") != "pop"]

    # The first segment is always intentionally hook. Verify `screen` through
    # an explicit planner label, as the AI classifier can emit it directly.
    ui = PL.build([seg(0.0, 3.2, "IKKI app dashboard ကိုပြမယ်")], ["screen"],
                  4.0, dict(energy="standard"), "ui1")
    ok_ui, err_ui, _ = PS.validate(ui, MF, duration=4.0)
    ui_ev = _gfx(ui)
    check("UI plan schema အောင်သည်", ok_ui, err_ui[:2])
    # ⚠️ **id အတိအကျ မစစ်ရ — မျိုးရိုးကို စစ်ရမည်** (၂၀၂၆-၀၉-၂၅)。
    #    ယခင်က `== "brows.window_open"` ဟု ရေးထားရာ candidate pool ကို
    #    ချဲ့ပြီး လှည့်ခြင်း ထည့်လိုက်သည်နှင့် ကျခဲ့သည် — ဒါပေမယ့် ရွေးလိုက်တာ
    #    `thm.ui_progress` (category `ui`) ဖြစ်၍ **semantic အရ မှန်**သည်。
    #    ဗီဒီယိုတိုင်း template တစ်ခုတည်း မဖြစ်စေရန် လှည့်ခြင်းက ရည်ရွယ်ချက်
    #    ဖြစ်သည် (Zin: 「မထပ်အောင်」) ⇒ ဂိတ်က **UI မျိုးရိုး** ကို စစ်ရမည်、
    #    id တစ်ခုတည်းကို မဟုတ်。 ဂိတ် လျှော့ခြင်း မဟုတ် — မှန်ရာကို စစ်ခြင်း。
    # ⚠️ category နဲ့ စစ်၍လည်း မရ — `thm.media_window` က `screen` ရဲ့
    #    ကိုယ်ပိုင် စာရင်းထဲ ပါပေမယ့် category က `infographic` ဖြစ်သည်。
    #    ⇒ စစ်ရမည့် **ဂုဏ်သတ္တိ**က 「`screen` ရဲ့ ကိုယ်ပိုင် pool ထဲကလား」
    #      ဖြစ်သည် — ယေဘုယျ pool (label တိုင်း နောက်က ဆက်တွဲထားသည်) ကနေ
    #      လာလျှင် semantic ရွေးချယ်မှု ပျက်ပြီဟု ဆိုလိုသည်。
    _uid = ui_ev[0]["motionKitTemplateId"] if ui_ev else ""
    _sc = PL._profile_candidates("screen", "premium", None)
    _gen = set(PL._auto_candidates("fact"))
    _k = len(_sc)
    while _k > 0 and _sc[_k - 1] in _gen:      # ယေဘုယျ အမြီးကို ဖြတ်
        _k -= 1
    check("UI event က `screen` ရဲ့ ကိုယ်ပိုင် pool ကနေ ရွေးသည်",
          bool(ui_ev) and _uid in set(_sc[:_k]),
          f"{_uid} · screen pool {_sc[:_k]}")
    check("UI event ကို full-stage အဖြစ် route လုပ်သည်",
          bool(ui_ev) and ui_ev[0]["style"].get("layout") == "full", ui_ev)
    ui_after_hook = PL.build([
        seg(0.0, 2.7, "ဒီနေ့ အရေးကြီးတဲ့အချက်ကို ပြမယ်"),
        seg(3.2, 6.2, "IKKI app dashboard screen ကိုပြမယ်"),
    ], ["hook", "screen"], 7.0, dict(energy="standard"), "ui2")
    ui_after_events = _gfx(ui_after_hook)
    check("hook နောက် UI reveal ကို pacing gap ကြောင့် မပျောက်",
          any((x.get("style") or {}).get("lab") == "screen"
              for x in ui_after_events), ui_after_events)
    check("full-stage UI နဲ့ keyword pop မထပ်",
          not _pops(ui_after_hook), _pops(ui_after_hook))
    tids = [x["motionKitTemplateId"] for x in _gfx(p)]
    # ⚠️ template က motionkit catalog **သို့မဟုတ်** verify ပြီးသား pack
    #    ကနေ လာနိုင်သည် — catalog တစ်ခုတည်းနဲ့ စစ်လျှင် pack template
    #    အားလုံး 「မရှိ」ဟု ကျမည် (၂၀၂၆-၀၉-၂၁ pack ချိတ်ချိန် ဖြစ်ခဲ့)。
    import pack as PK
    _ok = set(MF.ids()) | set(PK.selectable())
    check("template ID အားလုံး တကယ်ရှိသည်",
          all(c in _ok for c in tids), [c for c in tids if c not in _ok])
    # ⚠️ **ဘောင်အပြည့် ကတ်က တစ်ခါသာ** — ပြောသူကို တမင် ဖုံးသဖြင့်
    #    ထပ်ခါထပ်ခါ သုံးလျှင် talking-head က slideshow ဖြစ်သည်。
    _ff = [c for c in tids
           if (PK.template(c) or {}).get("fullFrame")] if True else []
    check("ဘောင်အပြည့် ကတ် ≤ ၁ ခု", len(_ff) <= 1, _ff)
    _ffe = [x for x in _gfx(p) if (PK.template(x["motionKitTemplateId"]) or {})
            .get("fullFrame")]
    check("ဘောင်အပြည့်က ဖွင့်ချက်မှာသာ",
          all((x.get("style") or {}).get("lab") == "hook" for x in _ffe),
          [(x["startTime"], (x.get("style") or {}).get("lab")) for x in _ffe])
    check("pack template က verify ပြီးသားသာ",
          all(c in set(PK.selectable()) for c in tids if str(c).startswith("headtop.")),
          [c for c in tids if str(c).startswith("headtop.")
           and c not in set(PK.selectable())])
    check("ဆက်တိုက် တူသော template မရှိ",
          all(a != b for a, b in zip(tids, tids[1:])), tids)

    ts = [x["startTime"] for x in _gfx(p)]
    gaps = [b - a for a, b in zip(ts, ts[1:])]
    check("ကြားကာလ ပစ်မှတ် ထိန်းသည်",
          all(g >= PL.ENERGY["standard"]["gap"] - 0.01 for g in gaps),
          [round(g, 1) for g in gaps])

    pun = p["cameraReframes"]
    check("punch ၁.၀၈ မကျော်",
          all(x["props"]["zoom"] <= PS.MAX_PUNCH for x in pun))
    check("punch သတိပေးချက် မရှိ",
          not any(x["code"].startswith("punch") for x in w), w)

    print("\n── ၃ခ · keyword pop (တိုင်းထားသော စတိုင်) ──")
    pops = _pops(p)
    check("pop ထွက်သည်", len(pops) >= 1, len(pops))
    # ⚠️ ယခင်က `kinetic.word_pop` **တစ်ခုတည်း** ဟု စစ်ခဲ့သည် — အဲဒါက
    #    hardcode ဖြစ်ခဲ့သဖြင့် pop အားလုံး တူတူ ဖြစ်ခဲ့သည် (တိုင်းချက်:
    #    ဝါကျ ၁၀ ကြောင်းမှာ ၃ ခါ)。 ယခု `assets/pop_ok.txt` (တစ်ခုချင်း
    #    ဆောက်ပြီး တိုင်းထားသော ၂၁ ခု) ကနေ လှည့်သည် ⇒ **pop family
    #    အတွင်း ရှိရမည်** ဟုသာ စစ်သည် (တကယ့် ရည်ရွယ်ချက်)。
    import planner as _PLmod
    _ok = set(_PLmod._pops())
    check("pop အားလုံး တိုင်းထားသော pool ထဲက",
          all(x["motionKitTemplateId"] in _ok for x in pops),
          sorted({x["motionKitTemplateId"] for x in pops}))
    check("pop pool က ၁၀ ခု ကျော်",
          len(_ok) >= 10, len(_ok))
    ds = [x["endTime"] - x["startTime"] for x in pops]
    check("ကြာချိန် ၂.၈–၅.၂s (တိုင်းထားသော p25–p75)",
          all(2.79 <= d <= 5.21 for d in ds), [round(d, 1) for d in ds])
    pt = sorted(x["startTime"] for x in pops)
    check("ကြားကာလ ဘောင် ထိန်းသည်",
          all(b - a >= 14.99 for a, b in zip(pt, pt[1:])),
          [round(b - a, 1) for a, b in zip(pt, pt[1:])])
    for x in pops:
        st = x["style"]
        check(f"{x['props']['text'][:12]} နေရာ ဘောင်ထဲ",
              0.12 - 1e-6 <= st["cx"] <= 0.86 + 1e-6 and
              0.20 - 1e-6 <= st["cy"] <= 0.81 + 1e-6, (st["cx"], st["cy"]))
    check("အရွယ် ၁၀%H (၁၀၈px @1080)",
          all(x["props"]["size"] == 109 for x in pops),
          [x["props"]["size"] for x in pops])
    check("အရောင် အဝါ", all(x["props"]["fill"] == PS.ACCENT for x in pops))
    # ⚠️ minimal မှာ pop မပါရ — 「ဂရပ်ဖစ် နည်းနည်း」ဟု ရွေးထားသူကို မပေးရ
    check("minimal မှာ pop မပါ",
          not _pops(PL.build(SEGS, labs, DUR, dict(energy="minimal"), "v1")))

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
    check("မသိသော အညွှန်းက ဂရပ်ဖစ် မထုတ်ပါ", not _gfx(q), _gfx(q))

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
