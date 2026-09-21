"""cards — Headtop Premium template test (Motion Kit Step 4)

⚠️ `assets/calib/refboard_2026.json` ကနေ တိုင်းယူထားသော ပုံစံများသာ —
   `concept_card` (v2 ၅ ခု) · `outline_title` (v5 ၃ ခု)。
⚠️ spec §11 — aspect ၂ မျိုးလုံး · overflow မရှိ · safe zone · မြန်မာ glyph。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import numpy as np      # noqa: E402
import cards as CD      # noqa: E402
import pack as PK       # noqa: E402

FAILED = []
MM = "ဂျပန်မှာ အလုပ်လုပ်ချင်တယ် ဆိုတာ မှန်လား"
ASPECTS = ((1920, 1080), (1080, 1920))


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def main():
    print("── ၁ · manifest ──")
    # ⚠️ အရေအတွက်ကို **ကိန်းသေ မရေးရ** — template ထပ်ထည့်တိုင်း test ကျမည်。
    #    「အားလုံး manifest မှန်」 ကိုသာ စစ်ရမည် (ဒါက တကယ့် ဂိတ်)。
    check("selectable ≥ ၂ ခု", len(PK.selectable()) >= 2, PK.selectable())
    _bad = [t["id"] for t in (PK.load()[0].get("templates") or [])
            if PK.check_manifest(t)]
    check("manifest မပြည့်စုံတာ မရှိ", not _bad, _bad)
    for tid in PK.selectable():
        m = PK.template(tid)
        check(f"{tid.split('.')[-1]} manifest မှန်", m is not None)
        check(f"{tid.split('.')[-1]} aspect ၂ မျိုး",
              set((m or {}).get("aspects") or []) == {"16:9", "9:16"})
        check(f"{tid.split('.')[-1]} fallback ရှိ", bool((m or {}).get("fallback")))
    check("intent နဲ့ ရွေးနိုင်", PK.by_intent("emphasis") ==
          ["headtop.ht_outline_title"], PK.by_intent("emphasis"))
    check("မရှိသော intent ⇒ ဗလာ", PK.by_intent("nope") == [])

    print("\n── ၂ · concept_card — aspect ၂ မျိုး ──")
    for W, H in ASPECTS:
        im = CD.concept_card(MM, "Tokutei ဗီဇာနဲ့ တိုက်ရိုက် ဝင်နည်း", W=W, H=H)
        check(f"{W}x{H} အရွယ် မှန်", im.size == (W, H), im.size)
        a = np.asarray(im)
        # ⚠️ စာသား **ဘောင်ထဲ** ရှိရမည် — အဖြူ pixel နဲ့ စစ်သည်
        lum = a[..., :3].mean(2)
        ys, xs = np.nonzero(lum > 180)
        check(f"{W}x{H} စာသား ရှိသည်", len(xs) > 500, len(xs))
        if len(xs):
            check(f"{W}x{H} ဘေးအနား မထိ",
                  xs.min() >= W * 0.04 and xs.max() <= W * 0.96,
                  (xs.min() / W, xs.max() / W))
            # ⚠️ စာတန်းဇုန် (အောက် ၁၈%) ထဲ မဝင်ရ
            check(f"{W}x{H} စာတန်းဇုန် မထိ", ys.max() <= H * 0.83,
                  ys.max() / H)

    print("\n── ၃ · outline_title — အတွင်း ပွင့်လင်းရမည် ──")
    # ⚠️ အတွင်း ဖြည့်လျှင် ပြောသူကို ဖုံးသည် (reference က အနားသတ်သာ)
    for W, H in ASPECTS:
        im = CD.outline_title("အဓိက သော့ချက် သုံးချက်", W=W, H=H, cy=0.30)
        check(f"{W}x{H} အရွယ် မှန်", im.size == (W, H))
        al = np.asarray(im)[..., 3]
        ys, xs = np.nonzero(al > 16)
        check(f"{W}x{H} မင် ရှိသည်", len(xs) > 200, len(xs))
        if len(xs):
            check(f"{W}x{H} ဘောင်ထဲ",
                  xs.min() >= W * 0.02 and xs.max() <= W * 0.98,
                  (xs.min() / W, xs.max() / W))
            # ⚠️ အနားသတ်သာ ⇒ ink ရဲ့ bbox အတွင်း **အပြည့် မဖုံးရ**
            box = al[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            cover = (box > 16).mean()
            check(f"{W}x{H} အတွင်း ပွင့်လင်း (ဖုံး {cover*100:.0f}% < ၃၀%)",
                  cover < 0.30, cover)

    print("\n── ၄ · halo — တိုင်းပြီးမှ ခံရမည် ──")
    # ⚠️ အမြဲ ခံလျှင် အမှောင်မှာ ညစ် · မခံလျှင် အလင်းမှာ ပျောက်
    im0 = CD.outline_title("စမ်းသပ်", cy=0.3, halo=0.0)
    im1 = CD.outline_title("စမ်းသပ်", cy=0.3, halo=1.0)
    n0 = int((np.asarray(im0)[..., 3] > 16).sum())
    n1 = int((np.asarray(im1)[..., 3] > 16).sum())
    check("halo ခံလျှင် မင် ပိုများသည်", n1 > n0 * 1.2, (n0, n1))
    check("halo ၀ ⇒ အနားသတ်သာ", n0 > 100, n0)

    print("\n── ၅ · စာရှည်လျှင် မပြတ်ရ ──")
    # ⚠️ 「never squeeze unreadable text」⇒ ချုံ့ရမည်၊ ဖြတ်လို့ မရ
    long = "ဂျပန်မှာ အလုပ်လုပ်ချင်တဲ့သူတွေအတွက် အရေးအကြီးဆုံး အချက်သုံးချက်ကို ပြောပြပါမယ်"
    im = CD.concept_card(long, W=1920, H=1080)
    a = np.asarray(im)[..., :3].mean(2)
    ys, xs = np.nonzero(a > 180)
    check("ရှည်သော စာ ဘောင်ထဲ ဝင်သည်",
          len(xs) > 0 and xs.min() >= 1920 * 0.03 and xs.max() <= 1920 * 0.97,
          (xs.min() / 1920, xs.max() / 1920) if len(xs) else None)

    print("\n── ၆ · token ကနေ font ယူသည် ──")
    _, t = PK.load()
    check("display = MyanmarHeadOne",
          PK.tok(t, "type", "display") == "MyanmarHeadOne")

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
