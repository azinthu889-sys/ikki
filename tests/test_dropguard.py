# -*- coding: utf-8 -*-
"""`_drop_exact` ကာကွယ်ချက် — စကားထဲ ဖြတ်ခြင်း မဖြစ်စေရ (Cut audit P0)

⚠️ အရင်က သုံးစွဲသူ ပေးထားသော အပိုင်းကို **စစ်ဆေးမှု မရှိဘဲ** ဖြတ်ခဲ့သည်。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))
import cut as C     # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


# စကား run — 2–5s · 8–12s · 15–19s
SP = [(2.0, 5.0), (8.0, 12.0), (15.0, 19.0)]
DUR = 25.0


def main():
    print("── ၁ · တိတ်ဆိတ်မှုထဲ ဖြတ်ချက် ⇒ ခွင့်ပြု ──")
    ok, bad = C.validate_drops([[5.5, 7.5]], SP, DUR)
    check("ခွင့်ပြုသည်", len(ok) == 1 and not bad, (ok, bad))

    print("\n── ၂ · စကားထဲ ကျသော အစွန်း ⇒ ပိတ် ──")
    for d, lbl in (([[3.0, 7.5]], "အစ"), ([[5.5, 9.0]], "အဆုံး"),
                   ([[3.0, 9.0]], "အစ+အဆုံး"), ([[3.0, 4.0]], "နှစ်ဖက်လုံး စကားထဲ")):
        ok, bad = C.validate_drops(d, SP, DUR)
        check(f"{lbl} ⇒ ပိတ်သည်", not ok and len(bad) == 1, (ok, bad))
        check(f"{lbl} ⇒ အကြောင်းရင်း ပါ",
              bool(bad and "စကား" in bad[0][1]), bad)

    print("\n── ၃ · ကိန်း မမှန် ⇒ ပိတ် ──")
    for d, lbl in (([[float("nan"), 7.0]], "NaN"),
                   ([[float("inf"), 7.0]], "inf"),
                   ([[7.0, 6.0]], "အဆုံး < အစ"),
                   ([["a", "b"]], "စာသား"),
                   ([[-1.0, 1.0]], "အနုတ်"),
                   ([[6.0, 99.0]], "ကြာချိန် ကျော်")):
        ok, bad = C.validate_drops(d, SP, DUR)
        check(f"{lbl} ⇒ ပိတ်သည်", not ok and len(bad) == 1, (ok, bad))

    print("\n── ၄ · တိုလွန်း ⇒ ပိတ် ──")
    ok, bad = C.validate_drops([[6.0, 6.02]], SP, DUR)
    check("၀.၀၂s ⇒ ပိတ်", not ok and bad, (ok, bad))

    print("\n── ၅ · ထပ်နေသော အပိုင်း ⇒ ဒုတိယကို ပိတ် ──")
    ok, bad = C.validate_drops([[5.5, 7.5], [6.0, 7.0]], SP, DUR)
    check("တစ်ခုသာ ခွင့်ပြု", len(ok) == 1 and len(bad) == 1, (ok, bad))
    check("ထပ်နေကြောင်း ပြော", bool(bad and "ထပ်" in bad[0][1]), bad)

    print("\n── ၆ · အားလုံး ဖျက်လျှင် ဗီဒီယို မကျန် ⇒ တစ်ခုမှ မဖျက် ──")
    # ⚠️ ဗီဒီယို တစ်ခုလုံး ပျောက်သွားတာက အဆိုးဆုံး ရလဒ်
    ok, bad = C.validate_drops([[5.5, 7.5], [12.5, 14.5]], SP, DUR, kept=4.0)
    check("တစ်ခုမှ မဖျက်", not ok and len(bad) == 2, (ok, bad))
    ok, bad = C.validate_drops([[5.5, 7.5]], SP, DUR, kept=20.0)
    check("လုံလောက်လျှင် ဖျက်သည်", len(ok) == 1, (ok, bad))

    print("\n── ၇ · ဗလာ / None ──")
    check("None ⇒ ဗလာ", C.validate_drops(None, SP, DUR) == ([], []))
    check("ဗလာ ⇒ ဗလာ", C.validate_drops([], SP, DUR) == ([], []))

    print("\n── ၈ · စကား မြေပုံ မရှိလျှင်လည်း ကိန်း စစ်ရမည် ──")
    ok, bad = C.validate_drops([[7.0, 6.0]], [], DUR)
    check("sp ဗလာ ⇒ ကိန်းအမှား ဖမ်းသေးသည်", not ok and len(bad) == 1, (ok, bad))

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
