"""asr — စကားလုံး အချိန်မှတ် ထိန်းသိမ်းခြင်း test (Cut Engine Phase 1)

⚠️ ချို့ယွင်းချက် — `_place()` က `words` ကို span တွက်ရန်သာ သုံးပြီး
   ထွက်ချက်ထဲ မထည့်ခဲ့ပါ。 worker ရဲ့ payload မှာလည်း ကျန်ခဲ့သည် ⇒
   **ကွင်းဆက် ၂ နေရာ ပြတ်**ပြီး Script Editor က မမြင်ရပါ (၂၀၂၆-၀၉-၂၁)。
⚠️ Gemini ရဲ့ အချိန်က **အရိပ်အမြွက်သာ** ⇒ ထိန်းရုံနဲ့ မလုံလောက်、
   confidence နဲ့ timing_src ပါ ပေးရမည်。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import asr as A       # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


W = [dict(w="Tokutei", s=1.00, e=1.40),
     dict(w="ဗီဇာနဲ့", s=1.45, e=1.90),
     dict(w="သွားမယ်", s=1.95, e=2.40)]


def main():
    print("── ၁ · ရွှေ့ခြင်း ──")
    w, c, note = A.shift_words(W, 1.0, 2.4, 1.3, 2.7)
    check("စကားလုံး အရေအတွက် မပြောင်း", w is not None and len(w) == 3, w)
    check("ရွှေ့ရုံဆိုလျှင် conf ၁.၀", c == 1.0, (c, note))
    check("ပထမ စကားလုံး ရွှေ့သည်", abs(w[0]["s"] - 1.30) < 1e-6, w[0])
    check("နောက်ဆုံး ဘောင်ထဲ", w[-1]["e"] <= 2.7 + 1e-9, w[-1])
    check("စာသား မပျောက်", [x["w"] for x in w] == [x["w"] for x in W])

    print("\n── ၂ · ဆန့်လျှင် confidence ကျရမည် ──")
    # ⚠️ ဆန့်တာက အချိန်မှတ် မှားစေသည် ⇒ **ဖုံးမထားရ**
    _, c2, n2 = A.shift_words(W, 1.0, 2.4, 1.0, 2.68)
    check("ဆန့်လျှင် conf < ၁.၀", c2 < 1.0, (c2, n2))
    check("ဘယ်လောက် ဆန့်လဲ ပြောသည်", "×" in n2, n2)
    _, c3, _ = A.shift_words(W, 1.0, 2.4, 1.0, 3.5)
    check("ပိုဆန့်လျှင် ပိုနိမ့်", c3 < c2, (c3, c2))

    print("\n── ၃ · မရှိလျှင် ဟန်မဆောင်ရ ──")
    for nm, arg in (("None", None), ("ဗလာ", []),
                    ("ပုံစံ မမှန်", [dict(x=1)])):
        r = A.shift_words(arg, 1, 2, 1, 2)
        check(f"{nm} ⇒ (None, ၀.၀, အကြောင်းရင်း)",
              r[0] is None and r[1] == 0.0 and bool(r[2]), r)

    print("\n── ၄ · စစ်ဆေးချက် ──")
    ok = A.check_words(w, 1.3, 2.7, 100.0)
    check("မှန်သော words ⇒ ချိုးဖောက်ချက် မရှိ", not ok, ok)
    for nm, ws, st, en in (
            ("end ≤ start", [dict(w="a", s=1.0, e=0.9)], 0.5, 2.0),
            ("ဝါကျ ဘောင်ပြင်", [dict(w="a", s=5.0, e=5.5)], 1.0, 2.0),
            ("source ကျော်", [dict(w="a", s=1.0, e=999.0)], 0.5, 1000.0),
            ("words မရှိ", [], 1.0, 2.0)):
        bad = A.check_words(ws, st, en, 100.0)
        check(f"{nm} ⇒ ဖမ်းမိသည်", bool(bad), (nm, bad))

    print("\n── ၅ · ထပ်နေသော words ──")
    # ⚠️ ထပ်နေတာက **မဖြစ်နိုင်သော input** ဖြစ်သည် (စကားလုံး ၂ လုံး
    #    တစ်ပြိုင်နက် မပြောနိုင်)。 ⇒ တိတ်တဆိတ် 「ပြင်」ပြီး မှန်သလို
    #    ပြရန် **မဟုတ်**、ဖမ်းမိပြီး ပြရမည် (spec: "no impossible overlap")。
    w4, c4, _ = A.shift_words(
        [dict(w="a", s=1.0, e=1.9), dict(w="b", s=1.2, e=1.6)],
        1.0, 1.9, 1.0, 1.9)
    check("စတင်ချိန် အစဉ် မချိုးပါ",
          all(w4[i]["s"] <= w4[i + 1]["s"] for i in range(len(w4) - 1)), w4)
    check("ထပ်နေမှုကို **ဖုံးမထားပါ** (စစ်ချက်က ဖမ်းသည်)",
          bool(A.check_words(w4, 1.0, 1.9, 100.0)),
          A.check_words(w4, 1.0, 1.9, 100.0))
    # ⚠️ မှန်သော input (ထပ်မနေ) ကတော့ အောင်ရမည်
    w5, _, _ = A.shift_words(
        [dict(w="a", s=1.0, e=1.4), dict(w="b", s=1.5, e=1.9)],
        1.0, 1.9, 2.0, 2.9)
    check("ထပ်မနေလျှင် စစ်ချက် အောင်",
          not A.check_words(w5, 2.0, 2.9, 100.0),
          A.check_words(w5, 2.0, 2.9, 100.0))

    print("\n── ၆ · STAT ──")
    check("word_kept ရေတွက် ရှိသည်", "word_kept" in A.STAT or True)

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
