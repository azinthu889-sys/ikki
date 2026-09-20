"""asr.est_bias — ဖိုင်ကိုယ်တိုင်ကနေ bias တိုင်းခြင်း test

⚠️ Gemini **မခေါ်ပါ** — `est_bias()` · `align()` ကိုသာ စမ်းသည်。
⚠️ ဘာကြောင့် ရှိရသလဲ — `BIAS = 0.43` က **zjl ချန်နယ်** ကနေ တိုင်းယူထားတာ ဖြစ်ပြီး
   calib မရှိသော brand (ikki · zae) မှာ အတိအကျ ယူသုံးနေခဲ့သည်。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import numpy as np          # noqa: E402
import asr as A             # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def fixture(bias=0.30, n=20, gap=4.0, jitter=0.05, seed=7):
    """onset များနဲ့ **စောနေသော** ASR အချိန် — မှန်ကန်သော ပြင်ချက် = `bias`"""
    rng = np.random.default_rng(seed)
    on = [2.0 + gap * i for i in range(n)]
    raw = [(t - bias + float(rng.normal(0, jitter)), t + gap * 0.8) for t in on]
    return raw, on


def main():
    print("── ၁ · တိုင်းယူချက်က ချေးယူထားတာထက် ကောင်းရမည် ──")
    raw, on = fixture(bias=0.30)
    b, n = A.est_bias(raw, on)
    check("တိုင်းယူ၍ ရသည်", b is not None, b)
    if b is not None:
        e_meas, e_lend = abs(b - 0.30), abs(A.BIAS - 0.30)
        print(f"    တိုင်းယူ {b:+.3f}s (လွဲ {e_meas:.3f}) · "
              f"ချေးယူ {A.BIAS:+.3f}s (လွဲ {e_lend:.3f})")
        check("လွဲချက် ၀.၀၅s အောက်", e_meas < 0.05, e_meas)
        check("ချေးယူထားတာထက် ကောင်းသည်", e_meas < e_lend, (e_meas, e_lend))
    check("တွဲချက် အားလုံး ရသည်", n == len(raw), n)

    print("\n── ၂ · အစ ကိန်း မှားလည်း တည်ငြိမ်အမှတ် တူရမည် ──")
    got = {}
    for st in (A.BIAS, 0.0, -1.2):
        got[st], _ = A.est_bias(raw, on, start=st)
    print("    " + " · ".join(f"{k:+.2f}→{v:+.3f}" for k, v in got.items()))
    check("၃ မျိုးလုံး တူသည်", len(set(round(v, 2) for v in got.values())) == 1, got)

    print("\n── ၃ · မသေချာလျှင် မှန်းဆ မလုပ်ရ ──")
    # ⚠️ ဒါက အရေးကြီးဆုံး — မှန်းဆ လုပ်မိလျှင် ဝါကျ အားလုံး ရွှေ့သွားမည်
    b2, n2 = A.est_bias(raw[:4], on[:4])
    check("တွဲ နည်းလျှင် None", b2 is None, b2)
    check("တွဲ အရေအတွက် ပြန်ပေးသည်", n2 == 4, n2)
    b3, _ = A.est_bias(raw, on, start=2.5)
    check("alias (ဘောင်ကျော်) ကို ငြင်းသည်", b3 is None, b3)
    b4, n4 = A.est_bias([], on)
    check("ဗလာ ထည့်လျှင် None", b4 is None and n4 == 0, (b4, n4))

    print("\n── ၄ · ဘောင် ──")
    check("MIN_PAIRS ≥ ၈", A.MIN_PAIRS >= 8, A.MIN_PAIRS)
    check("MAX_BIAS ≤ ၁.၅s", A.MAX_BIAS <= 1.5, A.MAX_BIAS)

    print("\n── ၅ · ဆူညံသံ များလျှင်လည်း ခံနိုင်ရမည် ──")
    raw5, on5 = fixture(bias=0.30, jitter=0.20, seed=3)
    b5, _ = A.est_bias(raw5, on5)
    check("jitter ၀.၂၀s နဲ့လည်း ၀.၁s အတွင်း",
          b5 is not None and abs(b5 - 0.30) < 0.10, b5)

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
