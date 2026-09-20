"""ပုံစံ ထိန်းချုပ်ချက် — UI ခလုတ်တွေက **တကယ် သက်ရောက်ရမည်** test

⚠️ ဘာကြောင့် ရှိရသလဲ — ၂၀၂၆-၀၉-၂၁ စစ်တော့ `motion` · `broll_freq` ·
   `sfx_on` · `autocut` · `silence_ms` တို့က `BOUNDS` မှာ စစ်ပြီး DB မှာ
   သိမ်းပေမယ့် **worker က ဘယ်မှာမှ မဖတ်ခဲ့ပါ** ⇒ ခလုတ် ၅ ခု ဘာမှ မလုပ်ခဲ့ပါ。
⚠️ ဒုတိယ — ချိတ်ရင်း `silence_ms=400` ကို DEF မှာ ထားမိသဖြင့် ပုံစံတိုင်းရဲ့
   **တိုင်းထားသော `min_sil`** ကို ၀.၄၀ သို့ ပြားစေခဲ့သည် (cinematic-vlog
   ၁.၂၀ → ၀.၄၀)。 ⇒ ဒီဖိုင်က အဲဒီ ကိန်းတွေကို ကာကွယ်သည်。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import recipes as R        # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


# ⚠️ **တိုင်းထားသော ကိန်းများ** — ပြောင်းလျှင် ဒီဖိုင်ကိုပါ ပြင်ရမည်
MEASURED_MIN_SIL = {
    "cinematic-vlog": 1.2, "vlog": 0.75, "podcast": 0.45, "knowledge": 0.45,
    "ref-talk": 0.32, "headtop": 0.32, "short-video": 0.34, "course": None,
    "brand-review": 0.75, "short-biz": 0.38, "promotional": 0.4,
}


def main():
    print("── ၁ · တိုင်းထားသော min_sil မပြောင်းရ ──")
    for k, v in MEASURED_MIN_SIL.items():
        got = R.get(k)["min_sil"]
        check(f"{k} = {v}", got == v, got)

    print("\n── ၂ · silence_ms က min_sil ကနေ ဆင်းသက်ရမည် (တစ်လမ်းသွား) ──")
    for k, v in MEASURED_MIN_SIL.items():
        r = R.get(k)
        want = None if v is None else int(round(v * 1000))
        check(f"{k} → {want}", r.get("silence_ms") == want, r.get("silence_ms"))

    print("\n── ၃ · ခလုတ်တိုင်း တကယ် သက်ရောက်ရမည် ──")
    base = R.get("headtop")
    cases = [
        ("silence_ms", 700, "min_sil", 0.7),
        ("autocut", False, "keep_pause", None),
        ("sfx_on", False, "sfx", False),
        ("broll_freq", "high", "broll", int(round(base["broll"] * 1.5))),
        ("broll_freq", "low", "broll", int(round(base["broll"] * 0.5))),
        ("motion", "high", "zoom_amt", round(min(0.12, base["zoom_amt"] * 1.5), 4)),
        ("motion", "low", "zoom_amt", round(base["zoom_amt"] * 0.5, 4)),
    ]
    for key, val, eff, want in cases:
        a = R.apply("headtop", R.clean({key: val}))
        check(f"{key}={val!r} → {eff}={want!r}", a.get(eff) == want, a.get(eff))

    print("\n── ၄ · punch ၀.၁၂ ဘောင် မကျော်ရ ──")
    # ⚠️ ၁.၀၈ ဆ ကန့်သတ်ချက်က မျက်နှာ မပျက်စေရန် တိုင်းထားသော ကိန်း
    a = R.apply("headtop", R.clean(dict(zoom_amt=0.12, motion="high")))
    check("motion=high နဲ့လည်း ≤ ၀.၁၂", a["zoom_amt"] <= 0.12, a["zoom_amt"])

    print("\n── ၅ · မမှန်သော တန်ဖိုး လက်မခံရ ──")
    c = R.clean(dict(energy="turbo", motion="ကြီး", broll_freq="xx",
                     zoom_amt=0.99, silence_ms=99999))
    check("မရှိသော ရွေးချယ်မှု ပယ်သည်",
          not {"energy", "motion", "broll_freq"} & set(c), c)
    check("zoom_amt ဘောင်ထဲ ချသည်", c.get("zoom_amt") == 0.12, c.get("zoom_amt"))
    check("silence_ms ဘောင်ထဲ ချသည်", c.get("silence_ms") == 1200, c.get("silence_ms"))

    print("\n── ၆ · UI က မြင်ရမည့် field များ ──")
    h = [x for x in R.listing() if x["id"] == "headtop"][0]
    for k in ("plan", "energy", "motion", "sfx_on", "autocut",
              "broll_freq", "zoom_amt", "shot_grade", "silence_ms"):
        check(f"listing() မှာ {k} ပါသည်", k in h, sorted(h))
    check("plan မဟုတ်သော ပုံစံက plan=False",
          [x for x in R.listing() if x["id"] == "knowledge"][0]["plan"] is False)

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
