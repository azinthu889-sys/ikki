"""Headtop Premium — motion primitive test (Motion Kit Step 3)

⚠️ spec §5 — 「Each primitive needs deterministic start/end frames at
   24/25/30fps, alpha-safe output, and a visual regression fixture」。
⚠️ **flash frame မရှိရ** — ပထမ frame မှာ တစ်ချက် လင်းသွားခြင်း。
   `t=0` မှာ အတိအကျ ၀ ဖြစ်မှ ကင်းသည်。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def _load():
    import pack as PK
    d = PK.path("headtop-premium")
    if d not in sys.path:
        sys.path.insert(0, d)
    mk = os.path.dirname(os.path.dirname(d))
    if mk not in sys.path:
        sys.path.insert(0, mk)
    import primitives as P
    return P


FPS = (24.0, 25.0, 30.0)


def main():
    try:
        P = _load()
    except Exception as e:
        print(f"  ✗ primitives တင်၍ မရ: {type(e).__name__}: {e}")
        return 1

    print("── ၁ · token ကနေ ကြာချိန် ယူသည် ──")
    # ⚠️ ကုဒ်ထဲ ကိန်းသေ မရေးရ — token ပြောင်းလျှင် လိုက်ပြောင်းရမည်
    check("enter = တိုင်းချက် ၀.၄၆၇", abs(P.D("enter") - 0.467) < 1e-9, P.D("enter"))
    check("exit = တိုင်းချက် ၀.၂၀၀", abs(P.D("exit") - 0.200) < 1e-9, P.D("exit"))

    print("\n── ၂ · flash frame မရှိရ ──")
    for nm, f in (("fade", P.fade),):
        check(f"{nm} t=0 ⇒ အတိအကျ ၀", f(0.0) == 0.0, f(0.0))
        check(f"{nm} t<0 ⇒ ၀", f(-0.5) == 0.0, f(-0.5))
    check("scale t=0 ⇒ စတင် အရွယ်",
          abs(P.scale(0.0) - P.SCALE_IN[0]) < 1e-9, P.scale(0.0))
    check("slide t=0 ⇒ အကွာအဝေး အပြည့်",
          abs(P.slide(0.0, dist=48.0) - 48.0) < 1e-9, P.slide(0.0, dist=48.0))

    print("\n── ၃ · အဆုံး frame တိကျရမည် (fps ၃ မျိုး) ──")
    # ⚠️ **frame အညွှန်းနဲ့ ခေါ်ရမည်** — အချိန်နဲ့ တိုက်ရိုက် ခေါ်လျှင်
    #    ၂၄/၃၀fps မှာ နောက်ဆုံး frame က ကြာချိန်ထက် စောပြီး animation
    #    အပြည့် မရောက်ပါ (harness က ဖမ်းမိသော ချို့ယွင်းချက်)。
    for fps in FPS:
        n = P.frames(P.D("enter"), fps)
        check(f"{fps:.0f}fps frame ≥ ကြာချိန်", n / fps >= P.D("enter") - 1e-9,
              (n, n / fps))
        check(f"{fps:.0f}fps fade အဆုံး = ၁.၀",
              abs(P.at(P.fade, n, n) - 1.0) < 1e-9, P.at(P.fade, n, n))
        check(f"{fps:.0f}fps scale အဆုံး = ၁.၀",
              abs(P.at(P.scale, n, n) - 1.0) < 1e-9, P.at(P.scale, n, n))
        check(f"{fps:.0f}fps slide အဆုံး = ၀",
              abs(P.at(P.slide, n, n)) < 1e-9, P.at(P.slide, n, n))
        check(f"{fps:.0f}fps ပထမ frame = ၀",
              P.at(P.fade, 0, n) == 0.0, P.at(P.fade, 0, n))

    print("\n── ၄ · တစ်လမ်းသွား (monotonic) ──")
    # ⚠️ ခုန်မှု (overshoot) က business ပုံသေ မဟုတ် ⇒ တစ်လမ်းသွား ဖြစ်ရမည်
    for nm, f, rev in (("fade", P.fade, False), ("scale", P.scale, False),
                       ("slide", P.slide, True)):
        d = P.D("enter")
        v = [f(d * i / 60.0) for i in range(61)]
        mono = all(v[i] <= v[i + 1] + 1e-12 for i in range(60)) if not rev \
            else all(v[i] >= v[i + 1] - 1e-12 for i in range(60))
        check(f"{nm} တစ်လမ်းသွား", mono, v[:4])
        check(f"{nm} ဘောင်ကျော် မရှိ (ခုန်မှု မပါ)",
              min(v) >= (0.0 if nm != "scale" else P.SCALE_IN[0]) - 1e-9
              and max(v) <= (48.0 if nm == "slide" else 1.0) + 1e-9,
              (min(v), max(v)))

    print("\n── ၅ · တူညီသော input ⇒ တူညီသော output ──")
    a = [P.fade(t / 100.0) for t in range(50)]
    b = [P.fade(t / 100.0) for t in range(50)]
    check("determinstic", a == b)

    print("\n── ၆ · spec ဘောင် စစ်ချက် ──")
    # ⚠️ တိုင်းချက်က spec ဘောင်ထက် ရှည်သည် ⇒ **ပိတ်ခြင်း မဟုတ်**、ပြောခြင်း
    w = P.check("fade", P.D("enter"))
    check("band ကျော်လျှင် ပြောသည်", bool(w), w)
    check("ဘယ်လောက် ကျော်လဲ ပြောသည်", "band" in w[0] or "ဘောင်" in w[0], w)
    check("ဘောင်ထဲဆိုလျှင် တိတ်နေသည်", not P.check("fade", 0.22))
    check("stagger ဘောင် ၅၀–၉၀ms",
          not P.check("stagger", P.D("stagger")), P.D("stagger"))

    print("\n── ၇ · stagger ──")
    check("၀ ခုမြောက် ⇒ ၀", P.stagger(0) == 0.0)
    check("တစ်ခုချင်း တိုးသည်",
          abs(P.stagger(3) - 3 * P.D("stagger")) < 1e-9, P.stagger(3))

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
